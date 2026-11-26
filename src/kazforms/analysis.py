"""Read Apertium-kaz analyser output and reduce it to one noun analysis per word form.

The analyser prints one lexical unit per word: ^form/analysis/analysis/...$ with analyses such as
  қала<n><pl><px3sp><abl>
A reading with a "+" is a clitic (the copula, +е<cop>...) and is ignored. A form is kept only when
every other reading has the same lemma and exactly one distinct plain noun analysis is left.
Plain noun analysis: <n> [<pl>] [<pxNN> [<frm>]] <case>, with <attr>, <subst> and <err_orth>
readings treated as other uses of the same string (attributive, substantivised) or as misspellings.
"""

import re
from dataclasses import dataclass

CASES = ["nom", "gen", "acc", "dat", "loc", "abl", "ins"]
CASE_NAMES = {
    "nom": "nominative",
    "gen": "genitive",
    "acc": "accusative",
    "dat": "dative",
    "loc": "locative",
    "abl": "ablative",
    "ins": "instrumental",
}
# Apertium possessive tag (plus <frm>) -> cell label. 3 covers singular and plural possessor.
POSSESSION = {
    (): "none",
    ("px1sg",): "1sg",
    ("px2sg",): "2sg",
    ("px2sg", "frm"): "2sg.formal",
    ("px3sp",): "3",
    ("px1pl",): "1pl",
}
POSS_ORDER = ["none", "1sg", "2sg", "2sg.formal", "3", "1pl"]
POSS_TAGS = {v: k for k, v in POSSESSION.items()}

_UNIT = re.compile(r"^\^([^/]+)/(.*)\$$")
_TAG = re.compile(r"<([^>]+)>")


@dataclass(frozen=True)
class NounAnalysis:
    form: str
    lemma: str
    number: str  # sg | pl
    possession: str  # one of POSS_ORDER
    case: str  # one of CASES
    tags: str  # the Apertium tag string, e.g. <n><pl><px3sp><abl>
    n_readings: int  # all non-clitic readings the analyser gave for the string


def _plain(tags: list[str]) -> tuple[str, str, str] | None:
    """(number, possession, case) of a plain noun analysis, or None."""
    if not tags or tags[0] != "n":
        return None
    rest = tags[1:]
    number = "sg"
    if rest and rest[0] == "pl":
        number, rest = "pl", rest[1:]
    px: list[str] = []
    while rest and (rest[0].startswith("px") or (px and rest[0] == "frm")):
        px.append(rest[0])
        rest = rest[1:]
    if len(rest) != 1 or rest[0] not in CASES:
        return None
    poss = POSSESSION.get(tuple(px))
    if poss is None:
        return None
    return number, poss, rest[0]


def parse_unit(line: str) -> NounAnalysis | None:
    m = _UNIT.match(line.rstrip("\n"))
    if not m:
        return None
    form, rest = m.groups()
    readings = [r for r in rest.split("/") if "+" not in r]
    if not readings or any(r.startswith("*") for r in readings):
        return None
    lemmas = {r.split("<", 1)[0] for r in readings}
    if len(lemmas) != 1:
        return None
    plain = set()
    for r in readings:
        t = _TAG.findall(r)
        p = _plain(t)
        if p is not None:
            plain.add((p, "".join(f"<{x}>" for x in t)))
    if len(plain) != 1:
        return None
    (number, poss, case), tagstr = next(iter(plain))
    return NounAnalysis(form, lemmas.pop(), number, poss, case, tagstr, len(readings))
