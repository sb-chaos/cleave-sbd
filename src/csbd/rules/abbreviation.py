"""Standard abbreviations, honorifics, list item identifiers, and numeric rules."""

from __future__ import annotations

import re
import string

from csbd.rules.disambiguation import Rule
from csbd.rules.pua import PUA_NEWLINE, PUA_PERIOD

# =============================================================================
# Standard Abbreviations & Honorifics
# =============================================================================

# fmt: off
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
# Pre-Compiled Number & AM/PM Transformation Rules
# =============================================================================

# Consolidates leading numbers, decimals, and list enumerators (1., 12., 999.)
NUMBER_RULES: tuple[Rule, ...] = (
    Rule(re.compile(r"\.(?=\d)"), PUA_PERIOD),
    Rule(re.compile(r"(?<=\d)\.(?=\S)"), PUA_PERIOD),
    Rule(
        re.compile(rf"((?:(?<=^)|(?<=[\r\n{PUA_NEWLINE}]))\d{{1,3}})\.(?=\s\S|\))"),
        r"\g<1>" + PUA_PERIOD,
    ),
)

# Unmasks terminal period in a.m. / p.m. ONLY when it ends a sentence before a capitalized word
AM_PM_RULES: tuple[Rule, ...] = (
    Rule(
        re.compile(rf"(?<=\b[AaPp]{PUA_PERIOD}[Mm]){PUA_PERIOD}(?=\s[A-Z])"),
        ".",
    ),
)


# =============================================================================
# List Item Regexes
# =============================================================================

NUMBER_LIST_REGEX: re.Pattern[str] = re.compile(
    r"(?P<lead>(?:^|[\r\n]|\s)(?:[•⁃\-]\s*)?)"
    r"(?:(?P<lparen>\()(?P<num_p>\d{1,3})\)|(?P<num>\d{1,3})(?P<delim>\.\)?|\)))(?=\s|$)"
)
ALPHA_LIST_REGEX: re.Pattern[str] = re.compile(
    r"(?P<lead>(?:^|[\r\n]|\s)(?:[•⁃\-]\s*)?)"
    r"(?:(?P<lparen>\()(?P<letter_p>[a-z])\)|(?P<letter>[a-z])(?P<delim>\.\)?|\)))(?=\s|$)"
)
ROMAN_PARENS_REGEX: re.Pattern[str] = re.compile(
    r"(?P<lead>(?:^|[\r\n]|\s)(?:[•⁃\-]\s*)?)\((?P<roman>[ivxldcm]+)\)(?=\s|$)",
    re.IGNORECASE,
)
ROMAN_DELIM_REGEX: re.Pattern[str] = re.compile(
    r"(?P<lead>(?:^|[\r\n]|\s)(?:[•⁃\-]\s*)?)(?P<roman>[ivxldcm]+)(?P<delim>\.\)?|\))(?=\s|$)",
    re.IGNORECASE,
)


# =============================================================================
# Abbreviation Regexes & Roman/Latin Lookups
# =============================================================================

POSSESSIVE_ABBR_REGEX: re.Pattern[str] = re.compile(r"\.(?='s\b|’s\b|'S\b|’S\b)")
KOMMANDITGESELLSCHAFT_REGEX: re.Pattern[str] = re.compile(
    r"(?<=Co)\.(?=\s*(?:KG|GmbH|OHG|AG)\b)", re.IGNORECASE
)
SINGLE_UPPERCASE_LETTER_REGEX: re.Pattern[str] = re.compile(
    r"((?:(?<=^)|(?<=[\s\ue000]))(?:[A-ZА-ЯЁ]\.)+)(?=[,.:\-?!]|\s|\s*$)"
)
SINGLE_LOWERCASE_LETTER_REGEX: re.Pattern[str] = re.compile(
    r"((?:(?<=^)|(?<=\s))[a-zа-яё])\.(?=\s+[a-zA-Zа-яёА-ЯЁ]|\s*$)"
)
AM_PM_REGEX: re.Pattern[str] = re.compile(
    r"(?<=\d)\s*(?:a\.m|p\.m|am|pm)\b", re.IGNORECASE
)
MULTI_PERIOD_DEFAULT_REGEX: re.Pattern[str] = re.compile(
    r"\b[a-zA-Z\u0400-\u0500](?:\.[a-zA-Z\u0400-\u0500])+\.", re.IGNORECASE
)
ROMAN_UPPERCASE_FOLLOWING_REGEX: re.Pattern[str] = re.compile(r"\s+[A-Z]")


def build_compound_abbr_regex(compound_list: list[str]) -> re.Pattern[str] | None:
    """Build a regex matching compound abbreviations."""
    if not compound_list:
        return None
    compound_pattern: str = "|".join(re.escape(abbr) for abbr in compound_list)
    return re.compile(
        rf"((?:(?<=^)|(?<=\s))(?i:{compound_pattern}))"
        r"[\u200e\u200f\u202a-\u202e\u2066-\u2069]*\.?[\u200e\u200f\u202a-\u202e\u2066-\u2069]*"
        rf"(?=[.:\-?,!\"\'“”«»]|\s+(?:[a-zа-яё\u0600-\u06ff]|I\s|I'm|I'll|\d|\(|\"|'|«|„))"
    )


def build_prepositive_abbr_regex(prep_clean: list[str]) -> re.Pattern[str] | None:
    """Build a regex matching prepositive abbreviations."""
    if not prep_clean:
        return None
    prep_pattern: str = "|".join(re.escape(abbr) for abbr in prep_clean)
    return re.compile(rf"((?:(?<=^)|(?<=\s))(?i:{prep_pattern}))\.(?=(\s|:\d+))")


def build_number_abbr_regex(num_clean: list[str]) -> re.Pattern[str] | None:
    """Build a regex matching number-preceding abbreviations."""
    if not num_clean:
        return None
    num_pattern: str = "|".join(re.escape(abbr) for abbr in num_clean)
    return re.compile(rf"((?:(?<=^)|(?<=\s))(?i:{num_pattern}))\.(?=(\s*\d|\s+\())")


# Single linear scan pattern for standard abbreviations (evaluated with O(1) hash set lookup)
STANDARD_ABBR_SCAN_REGEX: re.Pattern[str] = re.compile(
    r"(?:(?<=^)|(?<=\s))(?P<word>[^\s\.\u200e\u200f\u202a-\u202e\u2066-\u2069]+)"
    r"(?P<lead_uni>[\u200e\u200f\u202a-\u202e\u2066-\u2069]*)\."
    r"(?P<trail_uni>[\u200e\u200f\u202a-\u202e\u2066-\u2069]*)"
    r"(?=[.:\-?,!\"\'“”«»]|\s+(?:[a-zа-яё\u0600-\u06ff]|I\s|I'm|I'll|\d|\(|\"|'|«|„))"
)


def build_standard_abbr_regex(std_clean: list[str]) -> re.Pattern[str] | None:
    """Build a regex matching standard abbreviations."""
    if not std_clean:
        return None
    std_pattern: str = "|".join(re.escape(abbr) for abbr in std_clean)
    return re.compile(
        rf"((?:(?<=^)|(?<=\s))(?i:{std_pattern}))"
        r"[\u200e\u200f\u202a-\u202e\u2066-\u2069]*\."
        r"[\u200e\u200f\u202a-\u202e\u2066-\u2069]*"
        rf"(?=[.:\-?,!\"\'“”«»]|\s+(?:[a-zа-яё\u0600-\u06ff]|I\s|I'm|I'll|\d|\(|\"|'|«|„))"
    )


def build_sentence_starters_boundary_regex(
    sentence_starters: frozenset[str],
) -> re.Pattern[str] | None:
    """Build a regex matching acronyms followed by sentence starters."""
    if not sentence_starters:
        return None
    starters_pattern: str = "|".join(
        re.escape(word) for word in sorted(sentence_starters, key=len, reverse=True)
    )
    return re.compile(
        rf"((?:U{PUA_PERIOD}S|U\.S|U{PUA_PERIOD}K|E{PUA_PERIOD}U|E\.U|"
        rf"U{PUA_PERIOD}S{PUA_PERIOD}A|U\.S\.A|I|i{PUA_PERIOD}v|I{PUA_PERIOD}V|i\.v|I\.V))"
        rf"{PUA_PERIOD}(?=\s+(?:{starters_pattern})\b)"
    )


def build_replace_all_dot_regex(non_dot: list[str]) -> re.Pattern[str] | None:
    """Build a regex matching non-dot abbreviations for full replacement."""
    if not non_dot:
        return None
    return re.compile(
        rf"((?:(?<=^)|(?<=\s))(?i:{'|'.join(re.escape(abbr) for abbr in non_dot)}))\."
    )


def build_replace_all_exact_regex(all_abbr_clean: list[str]) -> re.Pattern[str] | None:
    """Build a regex matching exact abbreviations for full replacement."""
    if not all_abbr_clean:
        return None
    return re.compile(
        rf"((?:(?<=^)|(?<=\s))(?i:{'|'.join(re.escape(abbr) for abbr in all_abbr_clean)}))(?=(\s|$|[.:\-?,!\"\'“”«»]))"
    )


ROMAN_NUMERALS: dict[str, int] = {
    roman: index
    for index, roman in enumerate(
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
ROMAN_NUMERALS_SET: frozenset[str] = frozenset(ROMAN_NUMERALS.keys())
LATIN_NUMERALS: dict[str, int] = {
    char: index for index, char in enumerate(string.ascii_lowercase)
}
