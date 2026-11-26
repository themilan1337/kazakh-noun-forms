"""Check that every row of data/ parses and agrees with its neighbours.

Usage: python3 -I scripts/check.py [DATA_DIR]      (default: data/ next to this script's folder)
Exit code 0 means every check passed.
"""

import csv
import math
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from kazforms.analysis import CASES, POSS_ORDER, POSS_TAGS  # noqa: E402

HEADER = ["Word", "Frequency", "Lexeme", "Case", "Number", "Possession", "Segmentation", "Apertium",
          "SplitLemma", "SplitCell", "SplitRandom"]
SPLITS = {"train", "dev", "test"}
ALPHABET = set("абвгғдеёжзийкқлмнңопрстуұүфхһцчшщъыіьэюяә")


def fail(msg: str) -> None:
    print("FAIL:", msg)
    sys.exit(1)


def main(data: Path) -> None:
    with open(data / "kazakh_nouns_10k.txt", encoding="utf-8", newline="") as f:
        rd = csv.reader(f, delimiter="\t")
        head = next(rd)
        if head != HEADER:
            fail(f"header {head}")
        rows = list(rd)
    words, lemma_split, cell_split = set(), {}, {}
    for k, r in enumerate(rows, start=2):
        if len(r) != len(HEADER):
            fail(f"line {k}: {len(r)} columns")
        w, freq, lemma, case, num, poss, seg, tags, sl, sc, sr = r
        if w in words:
            fail(f"line {k}: duplicate word {w}")
        words.add(w)
        if not (w and set(w) <= ALPHABET):
            fail(f"line {k}: {w!r} is not lower-case Kazakh Cyrillic")
        if int(freq) < 3:
            fail(f"line {k}: frequency {freq}")
        if case not in CASES or num not in ("sg", "pl") or poss not in POSS_ORDER:
            fail(f"line {k}: bad label {case} {num} {poss}")
        morphs = seg.split("-")
        if "".join(morphs) != w or any(not m for m in morphs):
            fail(f"line {k}: segmentation {seg} does not spell {w}")
        n_suffix = (num == "pl") + (poss != "none") + (case != "nom")
        if not (n_suffix <= len(morphs) - 1 <= n_suffix + 2 + (poss != "none")):
            fail(f"line {k}: {len(morphs)} morphs for {num} {poss} {case}")
        want = "<n>" + ("<pl>" if num == "pl" else "") + "".join(f"<{t}>" for t in POSS_TAGS[poss]) + f"<{case}>"
        if tags != want:
            fail(f"line {k}: Apertium {tags}, labels say {want}")
        if not {sl, sc, sr} <= SPLITS:
            fail(f"line {k}: split values {sl} {sc} {sr}")
        if lemma_split.setdefault(lemma, sl) != sl:
            fail(f"line {k}: lemma {lemma} is in two lemma splits")
        if cell_split.setdefault((num, poss, case), sc) != sc:
            fail(f"line {k}: cell {(num, poss, case)} is in two cell splits")
    # embeddings: same order, 300 finite numbers
    with open(data / "kazakh_noun_embeddings_10k.txt", encoding="utf-8") as f:
        n_emb = 0
        for k, (line, r) in enumerate(zip(f, rows, strict=False), start=1):
            parts = line.rstrip("\n").split(" ")
            if parts[0] != r[0]:
                fail(f"embedding row {k}: {parts[0]} vs {r[0]}")
            if len(parts) != 301 or not all(math.isfinite(float(x)) for x in parts[1:]):
                fail(f"embedding row {k} ({parts[0]}): {len(parts) - 1} numbers")
            n_emb += 1
        extra = sum(1 for _ in f)
    if n_emb != len(rows) or extra:
        fail(f"{n_emb} embedding rows (+{extra}) for {len(rows)} words")
    # the 50-row sample is a subset of the main file
    with open(data / "sample_50_for_check.csv", encoding="utf-8", newline="") as f:
        sample = list(csv.DictReader(f))
    index = {r[0]: r for r in rows}
    if len(sample) != 50:
        fail(f"sample has {len(sample)} rows")
    for s in sample:
        r = index.get(s["Word"])
        if r is None or [s["Lexeme"], s["Case"], s["Number"], s["Possession"], s["Segmentation"]] != [
            r[2], r[3], r[4], r[5], r[6]]:
            fail(f"sample row {s['Word']} differs from the main file")
    by = defaultdict(set)
    for r in rows:
        by[r[2]].add(r[3])
    print(f"OK: {len(rows)} rows, {len(by)} lemmas, {len(cell_split)} cells, {n_emb} embedding rows of 300, "
          f"{len(sample)} sample rows")


if __name__ == "__main__":
    main(Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).resolve().parents[1] / "data")
