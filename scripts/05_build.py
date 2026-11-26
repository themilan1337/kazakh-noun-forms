"""Step 5: segment, choose about 10,000 forms, add vectors and splits, write data/.

Usage: python3 -I scripts/05_build.py WORK_DIR OUT_DIR [TARGET_ROWS]
Inputs in WORK_DIR: candidates.tsv, gen.tsv, vectors.tsv (steps 3, generator run and 4).
Every random choice uses the fixed seed below, so the same inputs give the same files.
"""

import csv
import json
import random
import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from kazforms.analysis import CASES, POSS_ORDER, POSS_TAGS  # noqa: E402
from kazforms.segment import segment  # noqa: E402

SEED = 20261126
MIN_COUNT = 3  # a form must occur at least this often in the corpus
MIN_LEMMA_FORMS = 16  # a lemma needs this many usable attested forms to be chosen
LEMMA_CAP = 30  # at most this many rows per lemma
SAMPLE_SIZE = 50


def read_tsv(path: Path):
    with open(path, encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f, delimiter="\t"))


def load_generator(path: Path) -> dict[str, list[str]]:
    gen: dict[str, list[str]] = defaultdict(list)
    for line in path.read_text(encoding="utf-8").splitlines():
        parts = line.split("\t")
        if len(parts) == 3 and "+?" not in parts[1]:
            gen[parts[0]].append(parts[1])
    return gen


def pick(options: list[str], form: str) -> str | None:
    """Among alternative generated surfaces, the one that agrees longest with the corpus form."""
    if not options:
        return None
    return max(options, key=lambda s: (s == form, sum(1 for a, b in zip(s, form, strict=False) if a == b)))


def cell_of(r) -> tuple[str, str, str]:
    return (r["number"], r["possession"], r["case"])


def water_fill(sizes: dict, target: int) -> int:
    """Largest cap so that sum(min(size, cap)) <= target."""
    lo, hi = 1, max(sizes.values())
    while lo < hi:
        mid = (lo + hi + 1) // 2
        if sum(min(s, mid) for s in sizes.values()) <= target:
            lo = mid
        else:
            hi = mid - 1
    return lo


def split_cells(counts: dict, rng: random.Random, min_rows: int = 20) -> dict:
    """About 70/15/15 by cell. Cells with fewer than min_rows rows stay in train (too small to test on),
    and every number, possession and case value stays in train."""
    small = sorted(c for c, n in counts.items() if n < min_rows)
    big = sorted(c for c, n in counts.items() if n >= min_rows)
    for _ in range(10000):
        order = big[:]
        rng.shuffle(order)
        n = len(order)
        train, dev, test = order[: int(n * 0.7)], order[int(n * 0.7) : int(n * 0.85)], order[int(n * 0.85) :]
        keep = train + small
        if ({c[0] for c in keep} == {"sg", "pl"} and {c[1] for c in keep} == set(POSS_ORDER)
                and {c[2] for c in keep} == set(CASES)):
            return {**{c: "train" for c in keep}, **{c: "dev" for c in dev}, **{c: "test" for c in test}}
    raise RuntimeError("no cell split found")


def three_way(keys: list, rng: random.Random) -> dict:
    keys = sorted(keys)
    rng.shuffle(keys)
    n = len(keys)
    out = {}
    for i, k in enumerate(keys):
        out[k] = "train" if i < int(n * 0.8) else "dev" if i < int(n * 0.9) else "test"
    return out


def main(work: str, out_dir: str, target: int = 10000) -> None:
    w, out = Path(work), Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    rng = random.Random(SEED)
    cands = read_tsv(w / "candidates.tsv")
    gen = load_generator(w / "gen.tsv")
    vectors = {}
    for line in (w / "vectors.tsv").read_text(encoding="utf-8").splitlines():
        f, v = line.split("\t")
        vectors.setdefault(f, v)

    stats = Counter()
    usable = []
    for r in cands:
        stats["candidates"] += 1
        if int(r["count"]) < MIN_COUNT:
            continue
        lemma = r["lemma"]
        if lemma != lemma.lower():
            stats["dropped_capitalised_lemma"] += 1
            continue
        if r["form"] not in vectors:
            stats["dropped_not_in_fasttext_vocabulary"] += 1
            continue
        pl = "<pl>" if r["number"] == "pl" else ""
        px = "".join(f"<{t}>" for t in POSS_TAGS[r["possession"]])
        stages = [pick(gen.get(f"{lemma}<n><nom>", []), r["form"])]
        if pl:
            stages.append(pick(gen.get(f"{lemma}<n><pl><nom>", []), r["form"]))
        if px:
            stages.append(pick(gen.get(f"{lemma}<n>{pl}{px}<nom>", []), r["form"]))
        final = [s.lower() for s in gen.get(f"{lemma}{r['tags']}", [])]
        if r["form"] not in final:
            stats["dropped_generator_disagrees"] += 1
            continue
        if any(s is None for s in stages):
            stats["dropped_no_stage"] += 1
            continue
        morphs = segment(r["form"], [s.lower() for s in stages])
        if morphs is None:
            stats["dropped_no_segmentation"] += 1
            continue
        r = dict(r, morphs=morphs)
        usable.append(r)
    stats["usable_forms"] = len(usable)

    by_lemma = Counter(r["lemma"] for r in usable)
    good = {lm for lm, n in by_lemma.items() if n >= MIN_LEMMA_FORMS}
    pool = [r for r in usable if r["lemma"] in good]
    stats["lemmas_with_enough_forms"] = len(good)
    stats["pool_forms"] = len(pool)

    cells: dict[tuple, list] = defaultdict(list)
    for r in pool:
        cells[cell_of(r)].append(r)
    cap = water_fill({c: len(v) for c, v in cells.items()}, target)
    chosen: list = []
    per_lemma: Counter = Counter()
    for c in sorted(cells, key=lambda c: len(cells[c])):  # rarest cells first
        items = cells[c][:]
        rng.shuffle(items)
        items.sort(key=lambda r: per_lemma[r["lemma"]])  # stable: lemmas with fewer rows first
        take = []
        for r in items:
            if len(take) >= cap:
                break
            if per_lemma[r["lemma"]] >= LEMMA_CAP:
                continue
            take.append(r)
            per_lemma[r["lemma"]] += 1
        chosen.extend(take)
    chosen.sort(key=lambda r: (r["lemma"], POSS_ORDER.index(r["possession"]), r["number"], CASES.index(r["case"])))

    lemma_split = three_way(sorted({r["lemma"] for r in chosen}), rng)
    cell_split = split_cells(Counter(cell_of(r) for r in chosen), rng)
    forms = [r["form"] for r in chosen]
    rand_split = three_way(forms, rng)

    header = ["Word", "Frequency", "Lexeme", "Case", "Number", "Possession", "Segmentation", "Apertium",
              "SplitLemma", "SplitCell", "SplitRandom"]
    with open(out / "kazakh_nouns_10k.txt", "w", encoding="utf-8", newline="") as f:
        wr = csv.writer(f, delimiter="\t", lineterminator="\n")
        wr.writerow(header)
        for r in chosen:
            wr.writerow([r["form"], r["count"], r["lemma"], r["case"], r["number"], r["possession"],
                         "-".join(r["morphs"]), r["tags"], lemma_split[r["lemma"]],
                         cell_split[cell_of(r)], rand_split[r["form"]]])
    with open(out / "kazakh_noun_embeddings_10k.txt", "w", encoding="utf-8", newline="") as f:
        for r in chosen:
            f.write(r["form"] + " " + vectors[r["form"]] + "\n")

    sample = rng.sample(chosen, SAMPLE_SIZE)
    sample.sort(key=lambda r: (r["lemma"], r["form"]))
    with open(out / "sample_50_for_check.csv", "w", encoding="utf-8", newline="") as f:
        wr = csv.writer(f)
        wr.writerow(["Word", "Frequency", "Lexeme", "Case", "Number", "Possession", "Segmentation", "Check", "Notes"])
        for r in sample:
            wr.writerow([r["form"], r["count"], r["lemma"], r["case"], r["number"], r["possession"],
                         "-".join(r["morphs"]), "", ""])

    lem_counts = Counter(r["lemma"] for r in chosen)
    with open(out / "lemmas.tsv", "w", encoding="utf-8", newline="") as f:
        wr = csv.writer(f, delimiter="\t", lineterminator="\n")
        wr.writerow(["Lexeme", "Rows", "SplitLemma"])
        for lm in sorted(lem_counts):
            wr.writerow([lm, lem_counts[lm], lemma_split[lm]])
    cell_counts = Counter(cell_of(r) for r in chosen)
    with open(out / "cells.tsv", "w", encoding="utf-8", newline="") as f:
        wr = csv.writer(f, delimiter="\t", lineterminator="\n")
        wr.writerow(["Number", "Possession", "Case", "Rows", "SplitCell"])
        for c in sorted(cell_counts, key=lambda c: (c[0], POSS_ORDER.index(c[1]), CASES.index(c[2]))):
            wr.writerow([*c, cell_counts[c], cell_split[c]])

    summary = {
        "rows": len(chosen),
        "lemmas": len(lem_counts),
        "cells": len(cell_counts),
        "cell_cap": cap,
        "lemma_cap": LEMMA_CAP,
        "seed": SEED,
        "funnel": dict(stats),
        "rows_per_lemma_min_median_max": [
            min(lem_counts.values()), sorted(lem_counts.values())[len(lem_counts) // 2], max(lem_counts.values())],
        "split_lemma_rows": dict(Counter(lemma_split[r["lemma"]] for r in chosen)),
        "split_cell_rows": dict(Counter(cell_split[cell_of(r)] for r in chosen)),
        "split_random_rows": dict(Counter(rand_split[r["form"]] for r in chosen)),
        "frequency_min_median_max": [
            min(int(r["count"]) for r in chosen),
            sorted(int(r["count"]) for r in chosen)[len(chosen) // 2],
            max(int(r["count"]) for r in chosen)],
        "number": dict(Counter(r["number"] for r in chosen)),
        "possession": dict(Counter(r["possession"] for r in chosen)),
        "case": dict(Counter(r["case"] for r in chosen)),
    }
    (out / "build_summary.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2], int(sys.argv[3]) if len(sys.argv) > 3 else 10000)
