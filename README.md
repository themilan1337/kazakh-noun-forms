# Kazakh noun forms: 10,000 inflected forms with frequencies and embeddings

About 10,000 inflected Kazakh noun forms (9,996 rows, 694 lemmas, 82 paradigm cells), each with its lemma,
case, number, possessive, the split into morphs, a corpus frequency and a 300-dimensional fastText vector.
It is the larger version of the 100-noun list sent on 10 November 2026, in the same layout, made for training
and testing a discriminative lexicon model (for example with JudiLing) on held-out data.

Nothing here has been trained or evaluated. The analyses come from an analyser, not from a person; a native-speaker
check of a 50-row random sample is in progress (see Checking).

## Files (`data/`)

| File | What |
|---|---|
| `kazakh_nouns_10k.txt` | Tab-separated, UTF-8, header, one row per form. Word and frequency are the first two columns, as in the 100-noun file. |
| `kazakh_noun_embeddings_10k.txt` | One row per form, same order: the word, then 300 numbers, space separated, no header. Numbers are copied as printed in the fastText `.vec` file (4 decimals). |
| `sample_50_for_check.csv` | 50 random rows (seeded) with empty `Check` and `Notes` columns, for a by-eye check. |
| `lemmas.tsv`, `cells.tsv` | Rows per lemma with its lemma split; rows per cell with its cell split. |
| `build_summary.json` | Counts at every filtering step, seed, split sizes. |

Columns of `kazakh_nouns_10k.txt`:

| Column | Meaning |
|---|---|
| `Word` | The inflected form, lower-case Cyrillic. Unique. |
| `Frequency` | Count of this exact spelling in the corpus below (case-folded). Every row has at least 3. |
| `Lexeme` | The lemma, from the Apertium-kaz analysis. |
| `Case` | `nom gen acc dat loc abl ins`. |
| `Number` | `sg` or `pl`. |
| `Possession` | `none`, `1sg`, `2sg`, `2sg.formal`, `3` (singular or plural possessor, the form is the same), `1pl`. |
| `Segmentation` | Surface morphs joined by `-`, in the order stem, plural, possessive, case (`қала-лар-ы-нан`). Where the stem changes before a vowel suffix the changed stem is the first morph (`кітаб-ым`, `халқ-ым`, `байлығ-ы`); 773 rows do this. |
| `Apertium` | The analyser's tag string, for example `<n><pl><px3sp><abl>`. |
| `SplitLemma`, `SplitCell`, `SplitRandom` | Proposed train / dev / test assignment under each of the three splits below. |

Rows per cell are capped at 272, so common cells are not larger than rare ones; some cells are small
(for example plural + 2sg + ablative has 1 row), because those forms are rare in news text.
Frequencies run from 3 to 6,706 (median 11); 4,478 rows are under 10. The set does not reproduce how often each
ending is used in real text: it was balanced by cell on purpose.

## Proposed splits

1. **By lemma** (`SplitLemma`, 80 / 10 / 10 of lemmas: 555 / 69 / 70 lemmas, 8,000 / 993 / 1,003 rows). Every form of a
   test lemma is in test. Asks whether the model generalises endings to words it has never seen.
2. **By cell** (`SplitCell`, 64 / 9 / 9 cells, 7,040 / 1,426 / 1,530 rows). Whole combinations of number, possessive and
   case are held out (for example singular + 3rd-person possessive + nominative), while every value of number,
   possessive and case still occurs in train. Cells with fewer than 20 rows stay in train. Every lemma of a test row also
   has forms in train. Asks whether the model builds forms of unseen combinations of endings.
3. **Random** (`SplitRandom`, 80 / 10 / 10 of forms), the plain baseline.

The splits are independent of each other; use one at a time.

## How the rows were made

1. **Corpus and frequency.** Leipzig Corpora Collection `kaz_newscrawl_2016_1M`: 1,000,000 Kazakh news sentences,
   15,185,892 running tokens, crawled 6-12 December 2016; archive dated 20 November 2020; downloaded 26 November 2026
   (sha256 `f1c88f1f3410eb47664d1e0848073e90106033d3db4d5c0dedc6a52e6353e31f`). Word types are lower-cased and their
   counts summed; types of 3 to 30 letters in the Kazakh Cyrillic alphabet are kept (329,844 types, 9,845,511 tokens).
2. **Analysis.** Every type went through the Apertium-kaz morphological analyser (commit
   `95c6dd0d8536ee69a7058634b03a3e82100b6b6e`, 1 Nov 2023, built in Docker with `apertium` 3.9.4, `lttoolbox` 3.7.6,
   `hfst` 3.16.0). A form is kept only if every reading (the copula clitic `+е<cop>` is ignored) has one lemma and there is
   exactly one plain noun analysis, `<n>` + optional `<pl>` + optional possessive + one case. Attributive,
   substantivised and `err_orth` readings of the same string are not counted as competing. That drops forms that are also
   other words (for example `қала`, "city" or the verb "stay"), so the frequency of a row is the frequency of that
   spelling with one analysis. Proper nouns (`<np>`) and capitalised lemmas are excluded. Forms the analyser accepts but its
   own generator does not produce (147) are dropped.
3. **Segmentation.** The generator half of the same analyser gives the surface of the lemma and of each cumulative
   prefix (lemma, plural, possessive, case); the morphs are the differences (`src/kazforms/segment.py`).
4. **Embeddings.** `cc.kk.300.vec` from the fastText Common Crawl + Wikipedia vectors (300 dimensions, trained before 2019).
   Only forms in the model's vocabulary are kept (761 candidates dropped), so no vector is built from character n-grams.
   The frequencies and the vectors come from different corpora.
5. **Choice of rows.** From 37,419 usable forms, lemmas with at least 16 usable forms were kept (694 lemmas, 15,820 forms),
   then a seeded draw takes up to 272 forms per cell, rarest cells first, at most 30 per lemma, preferring lemmas with the
   fewest rows so far. Result: 12 to 30 rows per lemma (median 14). Seed `20261126`; rebuilding gives byte-identical files.
6. **Overlap with the 100-noun file:** 41 of those 100 forms are also in this set (the others have a competing analysis or fell
   outside the lemma filter).

Counts: number sg 5,934, pl 4,062. Possession none 3,742, 3 3,661, 1pl 1,107, 1sg 881, 2sg 394, 2sg.formal 211.
Case nom 2,006, acc 1,677, dat 1,442, gen 1,418, abl 1,216, loc 1,151, ins 1,086.
Morphs per word: 1 in 272 rows, 2 in 2,892, 3 in 5,082, 4 in 1,750.

## Checking

`python3 -I scripts/check.py` parses every row and checks: columns, unique lower-case Cyrillic words, frequency at
least 3, labels, that the morphs spell the word, that the tag string matches the labels, that each lemma and each cell
sits in one split only, that the embedding file has the same words in the same order with 300 finite numbers, and that the
50-row sample is a subset of the main file. Last run: `OK: 9996 rows, 694 lemmas, 82 cells, 9996 embedding rows of 300, 50 sample rows`.

The 50-row sample (`sample_50_for_check.csv`) is for a check by a Kazakh speaker; its `Check` column is empty until that is done.
Known limits: the analyser can mislabel a rare or ambiguous form; a few strings are also another word that the analyser
does not know; Apertium covers some stems (for example vowel-dropping ones) differently from textbooks.

## Rebuild

`scripts/rebuild.sh [RAW_DIR]` downloads the two sources, builds the analyser image from `docker/Dockerfile`, and runs
steps 1-5 and the check. It needs python3 (3.10 or newer), curl, Docker, about 6 GB of disk. Downloads are
verified against the sha256 sums above and below.

## Sources and licences

| Part | Source | Licence |
|---|---|---|
| Frequencies | Leipzig Corpora Collection, `kaz_newscrawl_2016_1M`. Goldhahn, Eckart, Quasthoff (2012), "Building Large Monolingual Dictionaries at the Leipzig Corpora Collection: From 100 to 200 Languages", LREC 2012. (c) 2025 Universität Leipzig / Sächsische Akademie der Wissenschaften / InfAI. | The terms page says corpora offered for download are CC BY. (The page itself sits behind a bot check; we relied on two quotations of it, see NOTICE.) Counts only, no corpus text, are passed on. |
| Lemmas, tags, morphs | Apertium-kaz, https://github.com/apertium/apertium-kaz (commit above), run unmodified | GPL-3.0. The tool's output is given here as data; the tool and its lexicon are not included. |
| Embeddings | fastText `cc.kk.300.vec.gz`, https://dl.fbaipublicfiles.com/fasttext/vectors-crawl/cc.kk.300.vec.gz (sha256 `f1970ef87bb794363247fbaeb66cce24e03c9516dd1c74ca00499711c3ce1807`, file dated 18 Jan 2019). Grave, Bojanowski, Gupta, Joulin, Mikolov (2018), "Learning Word Vectors for 157 Languages", LREC 2018. | CC BY-SA 3.0 (https://fasttext.cc/docs/en/crawl-vectors.html) |
| Our files | This repository | Code: MIT (`LICENSE`). `kazakh_noun_embeddings_10k.txt`: CC BY-SA 3.0, like its source. Other files in `data/`: CC BY 4.0. Cite the sources above. |
