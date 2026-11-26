"""Step 1: case-folded Kazakh word types and counts from a Leipzig Corpora Collection words file.

Usage: python3 -I scripts/01_wordlist.py LEIPZIG_WORDS_FILE OUT_DIR
Writes OUT_DIR/types.tsv (form TAB count) and OUT_DIR/types.txt (one form per line, same order).
A type is kept when it is 3 to 30 letters of the Kazakh Cyrillic alphabet after lower-casing.
"""

import re
import sys
from collections import Counter
from pathlib import Path

KAZ = re.compile(r"^[абвгғдеёжзийкқлмнңопрстуұүфхһцчшщъыіьэюяә]{3,30}$")


def lower(w: str) -> str:
    # Kazakh dotted/dotless I and the usual lower-casing; Python's str.lower is enough for Cyrillic.
    return w.lower()


def main(words_file: str, out_dir: str) -> None:
    counts: Counter = Counter()
    n_lines = 0
    with open(words_file, encoding="utf-8") as f:
        for line in f:
            n_lines += 1
            _id, w, n = line.rstrip("\n").split("\t")
            lw = lower(w)
            if KAZ.match(lw):
                counts[lw] += int(n)
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    items = sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))
    (out / "types.tsv").write_text("".join(f"{w}\t{n}\n" for w, n in items), encoding="utf-8")
    (out / "types.txt").write_text("".join(f"{w}\n" for w, _ in items), encoding="utf-8")
    print(f"{n_lines} lines read, {len(items)} Kazakh word types kept, {sum(counts.values())} tokens")


if __name__ == "__main__":
    main(*sys.argv[1:3])
