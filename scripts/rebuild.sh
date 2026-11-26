#!/usr/bin/env bash
# Rebuild data/ from the two public downloads. Needs: python3 (3.10 or newer), curl, tar, shasum, Docker.
# About 6 GB of disk and 20 minutes (most of it the downloads and the one-off Docker build).
# Usage: scripts/rebuild.sh [RAW_DIR]     RAW_DIR defaults to ./raw (not committed)
set -euo pipefail
cd "$(dirname "$0")/.."
RAW="${1:-$PWD/raw}"
WORK="$RAW/work"
CORPUS_SHA=f1c88f1f3410eb47664d1e0848073e90106033d3db4d5c0dedc6a52e6353e31f
VEC_SHA=f1970ef87bb794363247fbaeb66cce24e03c9516dd1c74ca00499711c3ce1807

mkdir -p "$RAW/leipzig" "$RAW/fasttext" "$WORK"
if [ ! -f "$RAW/leipzig/kaz_newscrawl_2016_1M.tar.gz" ]; then
  curl -fsSL -o "$RAW/leipzig/kaz_newscrawl_2016_1M.tar.gz" \
    https://downloads.wortschatz-leipzig.de/corpora/kaz_newscrawl_2016_1M.tar.gz
fi
echo "$CORPUS_SHA  $RAW/leipzig/kaz_newscrawl_2016_1M.tar.gz" | shasum -a 256 -c -
[ -d "$RAW/leipzig/kaz_newscrawl_2016_1M" ] || tar -xzf "$RAW/leipzig/kaz_newscrawl_2016_1M.tar.gz" -C "$RAW/leipzig"
if [ ! -f "$RAW/fasttext/cc.kk.300.vec.gz" ]; then
  curl -fsSL -o "$RAW/fasttext/cc.kk.300.vec.gz" https://dl.fbaipublicfiles.com/fasttext/vectors-crawl/cc.kk.300.vec.gz
fi
echo "$VEC_SHA  $RAW/fasttext/cc.kk.300.vec.gz" | shasum -a 256 -c -

docker image inspect apertium-kaz-build >/dev/null 2>&1 || docker build -t apertium-kaz-build docker

python3 -I scripts/01_wordlist.py "$RAW/leipzig/kaz_newscrawl_2016_1M/kaz_newscrawl_2016_1M-words.txt" "$WORK"
docker run --rm -v "$WORK":/w apertium-kaz-build bash -c \
  'cd /opt/apertium-kaz && apertium -d . kaz-morph < /w/types.txt > /w/types.apertium'
python3 -I scripts/03_candidates.py "$WORK" 3
docker run --rm -v "$WORK":/w apertium-kaz-build bash -c \
  'cd /opt/apertium-kaz && hfst-lookup -q kaz.autogen.hfst < /w/gen_queries.txt > /w/gen.tsv'
python3 -I scripts/04_vectors.py "$RAW/fasttext/cc.kk.300.vec.gz" "$WORK"
python3 -I scripts/05_build.py "$WORK" data 10000
python3 -I scripts/check.py data
