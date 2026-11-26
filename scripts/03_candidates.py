"""Step 3: every word type with exactly one plain noun analysis, with its corpus count.

Usage: python3 -I scripts/03_candidates.py WORK_DIR [MIN_COUNT]
Reads WORK_DIR/types.tsv and WORK_DIR/types.apertium; writes WORK_DIR/candidates.tsv.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from kazforms.analysis import POSS_TAGS, parse_unit  # noqa: E402


def main(work: str, min_count: int = 3) -> None:
    w = Path(work)
    counts = {}
    for line in (w / "types.tsv").read_text(encoding="utf-8").splitlines():
        f, n = line.split("\t")
        counts[f] = int(n)
    rows, n_units = [], 0
    with open(w / "types.apertium", encoding="utf-8") as fh:
        for line in fh:
            n_units += 1
            a = parse_unit(line)
            if a is None or a.form not in counts or counts[a.form] < min_count:
                continue
            rows.append((a, counts[a.form]))
    with open(w / "candidates.tsv", "w", encoding="utf-8") as out:
        out.write("form\tcount\tlemma\tnumber\tpossession\tcase\ttags\tn_readings\n")
        for a, n in rows:
            out.write(f"{a.form}\t{n}\t{a.lemma}\t{a.number}\t{a.possession}\t{a.case}\t{a.tags}\t{a.n_readings}\n")
    # Generator queries: the lemma and each cumulative prefix of the analysis, to read the surface morphs.
    queries = set()
    for a, _ in rows:
        px = "".join(f"<{t}>" for t in POSS_TAGS[a.possession])
        pl = "<pl>" if a.number == "pl" else ""
        queries.add(f"{a.lemma}<n><nom>")
        if pl:
            queries.add(f"{a.lemma}<n><pl><nom>")
        if px:
            queries.add(f"{a.lemma}<n>{pl}{px}<nom>")
        queries.add(a.tags[:0] + f"{a.lemma}{a.tags}")
    (w / "gen_queries.txt").write_text("".join(q + "\n" for q in sorted(queries)), encoding="utf-8")
    print(f"{n_units} units read, {len(rows)} candidates with count >= {min_count}, "
          f"{len({a.lemma for a, _ in rows})} lemmas")


if __name__ == "__main__":
    main(sys.argv[1], int(sys.argv[2]) if len(sys.argv) > 2 else 3)
