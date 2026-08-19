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
MULTI_PERIOD_DEFAULT_REGEX = re.compile(r"\b[a-z](?:\.[a-z])+[.]", re.IGNORECASE)
POSSESSIVE_ABBR_REGEX = re.compile(r"\.(?='s\b|’s\b|'S\b|’S\b)")
KOMMANDITGESELLSCHAFT_REGEX = re.compile(r"(?<=Co)\.(?=\s*(?:KG|GmbH|OHG|AG)\b)", re.IGNORECASE)

# Single letter initials (e.g., "J. K. Rowling" -> "J\ue000 K\ue000 Rowling", "z. B." -> "z\ue000 B\ue000")
SINGLE_UPPERCASE_LETTER_REGEX = re.compile(r"(?:(?<=^)|(?<=\s))([A-ZА-ЯЁ])\.(?=\s+[a-zA-Zа-яёА-ЯЁ]|\s*$)")
SINGLE_LOWERCASE_LETTER_REGEX = re.compile(r"(?:(?<=^)|(?<=\s))([a-zа-яё])\.(?=\s+[a-zA-Zа-яёА-ЯЁ]|\s*$)")

# AM / PM Time Patterns
AM_PM_REGEX = re.compile(r"(?<=\d)\s*(?:a\.m|p\.m|am|pm)\b", re.IGNORECASE)


def replace_pre_number_abbr(txt: str, abbr: str) -> str:
    """Mask periods in number-preceding abbreviations (e.g. 'No. 5', 'pp. (1-3)')."""
    escaped_abbr = re.escape(abbr.strip())
    pattern = rf"((?:(?<=^)|(?<=\s)){escaped_abbr})\.(?=(\s\d|\s+\())"
    return re.sub(pattern, rf"\1{PUA_PERIOD}", txt, flags=re.IGNORECASE)


def replace_prepositive_abbr(txt: str, abbr: str) -> str:
    """Mask periods in prepositive titles and honorifics (e.g. 'Mr. Jones', 'Gen. 1:1')."""
    escaped_abbr = re.escape(abbr.strip())
    pattern = rf"((?:(?<=^)|(?<=\s)){escaped_abbr})\.(?=(\s|:\d+))"
    return re.sub(pattern, rf"\1{PUA_PERIOD}", txt, flags=re.IGNORECASE)


def replace_period_of_abbr(txt: str, abbr: str) -> str:
    """Mask standard abbreviation periods when followed by lowercase text, numbers, or punctuation."""
    escaped_abbr = re.escape(abbr.strip())
    pattern = (
        rf"((?:(?<=^)|(?<=\s)){escaped_abbr})\."
        rf"(?=[.:\-?,]|\s+(?:[a-z]|I\s|I'm|I'll|\d|\())"
    )
    return re.sub(pattern, rf"\1{PUA_PERIOD}", txt, flags=re.IGNORECASE)


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
        rf"U{PUA_PERIOD}S{PUA_PERIOD}A|U\.S\.A|I|i\.v|I\.V))"
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

    if not abbreviations and not prepositive and not number_abbr:
        return text

    lowered = text.lower()
    all_abbreviations = abbreviations | prepositive | number_abbr

    for abbr in all_abbreviations:
        stripped = abbr.strip()
        if not stripped or stripped not in lowered:
            continue

        # Check if candidate abbreviation exists at a word boundary
        match_pattern = re.compile(
            rf"(?:^|\s|\r|\n)({re.escape(stripped)})\.?(?=\s|$|\S)",
            re.IGNORECASE,
        )
        if not match_pattern.search(text):
            continue

        # Context check: character following the abbreviation
        next_char_pattern = re.compile(rf"(?<={re.escape(stripped)}\.\s)(\S)", re.IGNORECASE)
        next_chars = next_char_pattern.findall(text)
        char = next_chars[0] if next_chars else ""
        is_upper = char.isupper() if char else False

        normalized = stripped.lower()
        if not is_upper or normalized in prepositive:
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

    # 1. Structural & single-letter initials protection
    text = POSSESSIVE_ABBR_REGEX.sub(PUA_PERIOD, text)
    text = KOMMANDITGESELLSCHAFT_REGEX.sub(PUA_PERIOD, text)
    text = SINGLE_UPPERCASE_LETTER_REGEX.sub(rf"\1{PUA_PERIOD}", text)
    text = SINGLE_LOWERCASE_LETTER_REGEX.sub(rf"\1{PUA_PERIOD}", text)

    # 2. Language-specific custom preprocessing rules
    lang_module = get_language_module(lang) if lang else None
    lang_rules: tuple[Rule, ...] = getattr(lang_module, "RULES", ()) if lang_module else ()
    for rule in lang_rules:
        text = rule.pattern.sub(rule.replacement, text)

    # 3. Scan line-by-line against language abbreviation lexicon
    lines: list[str] = []
    for line in text.splitlines(keepends=True):
        lines.append(search_for_abbreviations_in_string(line, lang=lang))
    text = "".join(lines)

    # 4. Multi-period abbreviations (e.g., 'i.e.', 'e.g.', 'U.S.A.')
    text = replace_multi_period_abbreviations(text, lang=lang)

    # 5. Sentence boundary restoration for ambiguous abbreviations (e.g., '...in the U.S. The company...')
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
