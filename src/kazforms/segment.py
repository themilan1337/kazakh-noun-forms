"""Surface morphs of a form, read off the analyser's own generator.

The generator gives the surface of the lemma and of each cumulative prefix of the analysis
(lemma, +plural, +possessive, +case). Going back from the full form, each step either adds a
string to the end of the previous surface (қала + лар) or changes the end of the stem first
(кітап -> кітаб before ым, халық -> халқ before ы); then the changed part goes to the stem and the
suffix starts at the first vowel after the change.
"""

VOWELS = set("аәеёиіоөұүыэюя")


def common_prefix_len(a: str, b: str) -> int:
    n = 0
    for x, y in zip(a, b, strict=False):
        if x != y:
            break
        n += 1
    return n


def segment(form: str, stages: list[str]) -> list[str] | None:
    """stages: surfaces of the lemma and each prefix, shortest first (without the full form)."""
    cur = form
    suffixes: list[str] = []
    for prev in reversed(stages):
        if cur == prev:
            continue  # this step added nothing visible
        if cur.startswith(prev):
            suffixes.insert(0, cur[len(prev):])
            cur = prev
            continue
        lcp = common_prefix_len(cur, prev)
        rem = cur[lcp:]
        j = next((k for k, ch in enumerate(rem) if ch in VOWELS), None)
        if j is None:
            return None
        suffixes.insert(0, rem[j:])
        cur = cur[: lcp + j]
    morphs = [cur, *suffixes]
    if any(not m for m in morphs) or "".join(morphs) != form:
        return None
    return morphs
