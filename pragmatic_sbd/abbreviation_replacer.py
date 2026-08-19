"""Abbreviation disambiguation and replacement engine for sentence boundary detection.

Substitutes periods in honorifics, titles, acronyms, and language-specific abbreviations
with Unicode Private Use Area (PUA) sentinels (PUA_PERIOD: \ue000) to prevent false-positive
sentence splits.
"""

import re

from pragmatic_sbd.languages import get_language_module

from .lang.common.standard import (
    PUA_PERIOD,
    Rule,
)

# Common Pre-Compiled Patterns
MULTI_PERIOD_DEFAULT_REGEX = re.compile(
    r"\b[a-zA-Z\u0400-\u0500](?:\.[a-zA-Z\u0400-\u0500])+\.", re.IGNORECASE
)
POSSESSIVE_ABBR_REGEX = re.compile(r"\.(?='s\b|’s\b|'S\b|’S\b)")
KOMMANDITGESELLSCHAFT_REGEX = re.compile(r"(?<=Co)\.(?=\s*(?:KG|GmbH|OHG|AG)\b)", re.IGNORECASE)

# Single letter initials (e.g., "J. K. Rowling" -> "J\ue000 K\ue000 Rowling", "J.C. Penney" -> "J\ue000C\ue000 Penney")
SINGLE_UPPERCASE_LETTER_REGEX = re.compile(
    r"((?:(?<=^)|(?<=[\s\ue000]))[A-ZА-ЯЁ])\.(?=[,.:\-?!]|\s|[A-ZА-ЯЁ]\.|\s*$)"
)
SINGLE_LOWERCASE_LETTER_REGEX = re.compile(r"((?:(?<=^)|(?<=\s))[a-zа-яё])\.(?=\s+[a-zA-Zа-яёА-ЯЁ]|\s*$)")

# AM / PM Time Patterns
AM_PM_REGEX = re.compile(r"(?<=\d)\s*(?:a\.m|p\.m|am|pm)\b", re.IGNORECASE)


def replace_pre_number_abbr(txt: str, abbr: str) -> str:
    """Mask periods in number-preceding abbreviations (e.g. 'No. 5', 'pp. (1-3)')."""
    escaped_abbr = re.escape(abbr.strip())
    pattern = rf"((?:(?<=^)|(?<=\s))(?i:{escaped_abbr}))\.(?=(\s*\d|\s+\())"
    return re.sub(pattern, lambda m: m.group(1) + PUA_PERIOD, txt)


def replace_prepositive_abbr(txt: str, abbr: str) -> str:
    """Mask periods in prepositive titles and honorifics (e.g. 'Mr. Jones', 'Gen. 1:1')."""
    escaped_abbr = re.escape(abbr.strip())
    pattern = rf"((?:(?<=^)|(?<=\s))(?i:{escaped_abbr}))\.(?=(\s|:\d+))"
    return re.sub(pattern, lambda m: m.group(1) + PUA_PERIOD, txt)


def replace_period_of_abbr(txt: str, abbr: str) -> str:
    """Mask standard abbreviation periods when followed by lowercase text, numbers, or punctuation."""
    escaped_abbr = re.escape(abbr.strip())
    pattern = (
        rf"((?:(?<=^)|(?<=\s))(?i:{escaped_abbr}))\."
        rf"(?=[.:\-?,!\"\'“”«»]|\s+(?:[a-zа-яё]|I\s|I'm|I'll|\d|\(|\"|'|«|„))"
    )
    return re.sub(pattern, lambda m: m.group(1) + PUA_PERIOD, txt)


def replace_multi_period_abbreviations(text: str, lang: str = "") -> str:
    """Mask all periods inside multi-period acronyms and abbreviations."""
    lang_module = get_language_module(lang) if lang else None
    mpa_pattern: re.Pattern[str] = (
        getattr(lang_module, "MULTI_PERIOD_ABBREVIATION_REGEX", MULTI_PERIOD_DEFAULT_REGEX)
        if lang_module
        else MULTI_PERIOD_DEFAULT_REGEX
    )

    def _mask_periods(match: re.Match[str]) -> str:
        return match.group(0).replace(".", PUA_PERIOD)

    return mpa_pattern.sub(_mask_periods, text)


def replace_abbreviation_as_sentence_boundary(text: str, lang: str = "") -> str:
    """Restore terminal periods when an acronym is followed by a known sentence starter."""
    lang_module = get_language_module(lang) if lang else None
    sentence_starters: frozenset[str] = (
        getattr(lang_module, "SENTENCE_STARTERS", frozenset()) if lang_module else frozenset()
    )
    if not sentence_starters:
        return text

    starters_pattern = "|".join(re.escape(word) for word in sorted(sentence_starters, key=len, reverse=True))
    boundary_regex = re.compile(
        rf"((?:U{PUA_PERIOD}S|U\.S|U{PUA_PERIOD}K|E{PUA_PERIOD}U|E\.U|"
        rf"U{PUA_PERIOD}S{PUA_PERIOD}A|U\.S\.A|I|i{PUA_PERIOD}v|I{PUA_PERIOD}V|i\.v|I\.V))"
        rf"{PUA_PERIOD}(?=\s+(?:{starters_pattern})\b)"
    )
    return boundary_regex.sub(r"\1.", text)


def search_for_abbreviations_in_string(text: str, lang: str = "") -> str:
    """Scan string against all abbreviation sets defined in language configuration."""
    lang_module = get_language_module(lang) if lang else None
    abbreviations: frozenset[str] = (
        getattr(lang_module, "ABBREVIATIONS", frozenset()) if lang_module else frozenset()
    )
    prepositive: frozenset[str] = (
        getattr(lang_module, "PREPOSITIVE_ABBREVIATIONS", frozenset()) if lang_module else frozenset()
    )
    number_abbr: frozenset[str] = (
        getattr(lang_module, "NUMBER_ABBREVIATIONS", frozenset()) if lang_module else frozenset()
    )
    replace_all: bool = getattr(lang_module, "REPLACE_ALL_ABBR_PERIODS", False) if lang_module else False

    if not abbreviations and not prepositive and not number_abbr:
        return text

    lowered = text.lower()
    all_abbreviations = abbreviations | prepositive | number_abbr

    # Sort longest first to avoid partial matches on prefixes
    for abbr in sorted(all_abbreviations, key=len, reverse=True):
        stripped = abbr.strip()
        if not stripped:
            continue
        stripped_lowered = stripped.lower()
        if stripped_lowered not in lowered and stripped not in text:
            continue

        if replace_all:
            escaped_abbr = re.escape(stripped)
            if not stripped.endswith("."):
                pattern_dot = rf"((?:(?<=^)|(?<=\s)){escaped_abbr})\."
                text = re.sub(
                    pattern_dot,
                    lambda m: m.group(1).replace(".", PUA_PERIOD) + PUA_PERIOD,
                    text,
                    flags=re.IGNORECASE,
                )
            pattern_exact = rf"((?:(?<=^)|(?<=\s)){escaped_abbr})(?=(\s|$|[.:\-?,!\"\'“”«»]))"
            text = re.sub(
                pattern_exact,
                lambda m: m.group(1).replace(".", PUA_PERIOD),
                text,
                flags=re.IGNORECASE,
            )
            continue

        # Check if candidate abbreviation exists at a word boundary
        match_pattern = re.compile(
            rf"(?:^|\s|\r|\n)({re.escape(stripped)})\.?(?=\s|$|\S)",
            re.IGNORECASE,
        )
        if not match_pattern.search(text):
            continue

        normalized = stripped.lower()
        if normalized in prepositive:
            text = replace_prepositive_abbr(text, stripped)
        elif normalized in number_abbr:
            text = replace_pre_number_abbr(text, stripped)
        else:
            text = replace_period_of_abbr(text, stripped)

    return text


def replace_abbreviations(text: str, lang: str = "") -> str:
    """Stateless pure functional entrypoint for abbreviation disambiguation."""
    if not text:
        return text

    # 1. Structural & single-letter uppercase initials protection
    text = POSSESSIVE_ABBR_REGEX.sub(PUA_PERIOD, text)
    text = KOMMANDITGESELLSCHAFT_REGEX.sub(PUA_PERIOD, text)
    for _ in range(3):
        text = SINGLE_UPPERCASE_LETTER_REGEX.sub(lambda m: m.group(1) + PUA_PERIOD, text)

    # 2. Multi-period abbreviations (e.g., 'i.e.', 'e.g.', 'U.S.A.', 'т.б.')
    text = replace_multi_period_abbreviations(text, lang=lang)

    # 3. Language-specific custom preprocessing rules
    lang_module = get_language_module(lang) if lang else None
    lang_rules: tuple[Rule, ...] = getattr(lang_module, "RULES", ()) if lang_module else ()
    for rule in lang_rules:
        text = rule.pattern.sub(rule.replacement, text)

    # 4. Scan line-by-line against language abbreviation lexicon
    lines: list[str] = []
    for line in text.splitlines(keepends=True):
        lines.append(search_for_abbreviations_in_string(line, lang=lang))
    text = "".join(lines)

    # 5. Single-letter lowercase initials (e.g., 'z. B.')
    text = SINGLE_LOWERCASE_LETTER_REGEX.sub(lambda m: m.group(1) + PUA_PERIOD, text)

    # 6. AM/PM rules from common
    from .lang.common import common as common_module

    for rule in common_module.AM_PM_RULES:
        text = rule.pattern.sub(rule.replacement, text)

    # 7. Sentence boundary restoration for ambiguous abbreviations (e.g., '...in the U.S. The company...')
    text = replace_abbreviation_as_sentence_boundary(text, lang=lang)

    return text


class AbbreviationReplacer:
    """Disambiguates and masks abbreviations within text for a given language."""

    def __init__(self, text: str, lang: str = "") -> None:
        self.text = text
        self.lang = lang

    def replace(self) -> str:
        """Run full abbreviation disambiguation pipeline."""
        return replace_abbreviations(self.text, self.lang)

    def replace_abbreviation_as_sentence_boundary(self) -> None:
        self.text = replace_abbreviation_as_sentence_boundary(self.text, self.lang)

    def replace_multi_period_abbreviations(self) -> None:
        self.text = replace_multi_period_abbreviations(self.text, self.lang)

    def search_for_abbreviations_in_string(self, text: str) -> str:
        return search_for_abbreviations_in_string(text, self.lang)
