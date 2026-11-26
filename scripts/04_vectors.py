"""Step 4: pick the fastText vectors of the candidate forms out of cc.kk.300.vec.gz.

Usage: python3 -I scripts/04_vectors.py VEC_GZ WORK_DIR
Streams the gzip file (nothing is unpacked) and writes WORK_DIR/vectors.tsv: form TAB the 300 numbers
exactly as printed in the .vec file, space separated. Forms that are not in the model's vocabulary are
not written (the build drops them).
"""

import gzip
import sys
from pathlib import Path


def main(vec_gz: str, work: str) -> None:
    w = Path(work)
    wanted = {ln.split("\t", 1)[0] for ln in (w / "candidates.tsv").read_text(encoding="utf-8").splitlines()[1:]}
    found = 0
    with gzip.open(vec_gz, "rt", encoding="utf-8", errors="strict") as f, open(w / "vectors.tsv", "w", encoding="utf-8") as out:
        n_words, dim = map(int, f.readline().split())
        assert dim == 300, dim
        for line in f:
            word, _, rest = line.partition(" ")
            if word in wanted:
                nums = rest.split()
                assert len(nums) == 300, (word, len(nums))
                out.write(word + "\t" + " ".join(nums) + "\n")
                found += 1
    print(f"model vocabulary {n_words}, {len(wanted)} candidate forms, {found} found")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
