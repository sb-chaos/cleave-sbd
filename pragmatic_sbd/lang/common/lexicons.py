"""Standard vocabulary lexicons, abbreviations, numerals, and sentence starters."""

from __future__ import annotations

import re
import string

from .pua import PUA_EXCLAMATION

# =============================================================================
# Standard Punctuation & Sentence Starters
# =============================================================================

PUNCTUATIONS: frozenset[str] = frozenset({".", "!", "?", "\u3002", "\uff0e", "\uff01", "\uff1f"})

# fmt: off
SENTENCE_STARTERS: frozenset[str] = frozenset({
    "A", "Being", "Did", "For", "He", "How", "However", "I", "In", "It",
    "Millions", "More", "She", "That", "The", "There", "They", "We", "What",
    "When", "Where", "Who", "Why",
})

# =============================================================================
# Standard Abbreviations & Honorifics
# =============================================================================

STANDARD_ABBREVIATIONS: frozenset[str] = frozenset({
    "adj", "adm", "adv", "al", "ala", "alta", "apr", "arc", "ariz", "ark",
    "art", "assn", "asst", "attys", "aug", "ave", "bart", "bld", "bldg",
    "blvd", "brig", "bros", "btw", "cal", "calif", "capt", "cl", "cmdr",
    "co", "col", "colo", "comdr", "con", "conn", "corp", "cpl", "cres",
    "ct", "d.phil", "dak", "dec", "del", "dept", "det", "dist", "dr",
    "dr.phil", "dr.philos", "drs", "e.g", "ens", "esp", "esq", "etc",
    "exp", "expy", "ext", "feb", "fed", "fig", "fla", "ft", "fwy", "fy",
    "ga", "gen", "gov", "hon", "hosp", "hr", "hway", "hwy", "i.e", "ia",
    "id", "ida", "ill", "inc", "ind", "ing", "insp", "is", "jan", "jr",
    "jul", "jun", "kan", "kans", "ken", "ky", "la", "lt", "ltd", "maj",
    "man", "mar", "mass", "may", "md", "me", "med", "messrs", "mex",
    "mfg", "mich", "min", "minn", "miss", "mlle", "mm", "mme", "mo",
    "mont", "mr", "mrs", "ms", "msgr", "mssrs", "mt", "mtn", "neb",
    "nebr", "nev", "no", "nos", "nov", "nr", "oct", "ok", "okla", "ont",
    "op", "ord", "ore", "p", "pa", "pd", "pde", "penn", "penna", "pfc",
    "ph", "ph.d", "pl", "plz", "pp", "prof", "pvt", "que", "rd", "ref",
    "rep", "reps", "res", "rev", "rs", "rt", "sask", "sec", "sen",
    "sens", "sep", "sept", "sfc", "sgt", "sr", "st", "supt", "surg",
    "tce", "tenn", "tex", "u.s", "univ", "usafa", "ut", "v", "va",
    "ver", "viz", "vs", "vt", "wash", "wis", "wisc", "wy", "wyo", "yuk",
})

PREPOSITIVE_ABBREVIATIONS: frozenset[str] = frozenset({
    "adm", "attys", "brig", "capt", "cmdr", "col", "cpl", "det", "dr",
    "fig", "gen", "gov", "ing", "lt", "maj", "messrs", "mr", "mrs", "ms",
    "msgr", "mssrs", "mt", "ph", "prof", "rep", "reps", "rev", "sen",
    "sens", "sgt", "st", "supt", "v", "vs",
})

NUMBER_ABBREVIATIONS: frozenset[str] = frozenset({
    "art", "ext", "no", "nos", "p", "pp",
})
# fmt: on

# =============================================================================
# Exclamation Proper Nouns & Click Consonants
# =============================================================================

EXCLAMATION_WORDS: tuple[str, ...] = (
    "ǃʼOǃKung",
    "!Kung-Ekoka",
    "!Xuun",
    "ǃKhung",
    "ǃXung",
    "!Kung",
    "!Xun",
    "!Xũ",
    "ǃXû",
    "ǃXo",
    "ǃKu",
    "ǃHu",
    "ǃung",
    "Yahoo!",
    "Yum!",
    "Y!J",
)

EXCLAMATION_WORDS_REGEX: re.Pattern[str] = re.compile(
    "|".join(re.escape(w) for w in sorted(EXCLAMATION_WORDS, key=len, reverse=True))
)


def mask_exclamation_words(text: str) -> str:
    """Mask exclamation marks within known proper nouns and click consonants."""
    return EXCLAMATION_WORDS_REGEX.sub(
        lambda m: m.group(0).replace("!", PUA_EXCLAMATION),
        text,
    )


# =============================================================================
# Numerals & List Symbols
# =============================================================================

ROMAN_NUMERALS: dict[str, int] = {
    r: i
    for i, r in enumerate(
        (
            "i",
            "ii",
            "iii",
            "iv",
            "v",
            "vi",
            "vii",
            "viii",
            "ix",
            "x",
            "xi",
            "xii",
            "xiii",
            "xiv",
            "xv",
            "xvi",
            "xvii",
            "xviii",
            "xix",
            "xx",
        )
    )
}
ROMAN_NUMERALS_SET: frozenset[str] = frozenset(ROMAN_NUMERALS)
LATIN_NUMERALS: dict[str, int] = {c: i for i, c in enumerate(string.ascii_lowercase)}
