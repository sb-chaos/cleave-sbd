"""Language-specific abbreviation compilation, caching, and disambiguation."""

from __future__ import annotations

import re
from dataclasses import dataclass
from functools import lru_cache

from csbd.language.protocols import LanguageProtocol
from csbd.rules import (
    AM_PM_RULES,
    KOMMANDITGESELLSCHAFT_REGEX,
    MULTI_PERIOD_DEFAULT_REGEX,
    POSSESSIVE_ABBR_REGEX,
    PUA_PERIOD,
    SINGLE_LOWERCASE_LETTER_REGEX,
    SINGLE_UPPERCASE_LETTER_REGEX,
    STANDARD_ABBR_SCAN_REGEX,
    STANDARD_ABBREVIATIONS,
    build_compound_abbr_regex,
    build_number_abbr_regex,
    build_prepositive_abbr_regex,
    build_replace_all_dot_regex,
    build_replace_all_exact_regex,
    build_sentence_starters_boundary_regex,
)


@dataclass(slots=True, frozen=True)
class LanguageAbbreviationData:
    """Pre-compiled and cached regex patterns for language-specific abbreviation handling.

    Attributes:
        replace_all: Whether the language replaces all periods in abbreviations.
        compound_abbr_regex: Pattern matching compound multi-word abbreviations.
        prepositive_regex: Pattern matching prepositive honorifics.
        number_abbr_regex: Pattern matching abbreviations followed by numbers.
        standard_abbr_regex: Fallback pattern matching general standard abbreviations.
        standard_abbr_set: Invariant lowercase set of standard abbreviations for O(1) matching.
        replace_all_dot_regex: Pattern for replace-all dot abbreviations.
        replace_all_exact_regex: Pattern for replace-all exact abbreviations.
        sentence_boundary_starters_regex: Pattern identifying sentence boundary starters.
    """

    replace_all: bool
    compound_abbr_regex: re.Pattern[str] | None
    prepositive_regex: re.Pattern[str] | None
    number_abbr_regex: re.Pattern[str] | None
    standard_abbr_regex: re.Pattern[str] | None
    standard_abbr_set: frozenset[str]
    replace_all_dot_regex: re.Pattern[str] | None
    replace_all_exact_regex: re.Pattern[str] | None
    sentence_boundary_starters_regex: re.Pattern[str] | None


@lru_cache(maxsize=32)
def get_language_abbreviation_data(
    config: LanguageProtocol | None,
) -> LanguageAbbreviationData:
    """Pre-compile and cache unified category regexes per language.

    Args:
        config: Optional language configuration module.

    Returns:
        The pre-compiled abbreviation data structure for the given language.
    """
    lang_module = config
    if lang_module is not None:
        abbreviations: frozenset[str] = lang_module.abbreviations
        prepositive: frozenset[str] = lang_module.prepositive_abbreviations
        number_abbr: frozenset[str] = lang_module.number_abbreviations
        replace_all: bool = lang_module.replace_all_abbr_periods
        sentence_starters: frozenset[str] = lang_module.sentence_starters
    else:
        abbreviations = frozenset()
        prepositive = frozenset()
        number_abbr = frozenset()
        replace_all = False
        sentence_starters = frozenset()

    boundary_starters_regex: re.Pattern[str] | None = (
        build_sentence_starters_boundary_regex(sentence_starters)
    )

    if replace_all:
        all_abbr_clean = sorted(
            {
                abbr.strip()
                for abbr in (abbreviations | prepositive | number_abbr)
                if abbr.strip()
            },
            key=len,
            reverse=True,
        )
        non_dot = [abbr for abbr in all_abbr_clean if not abbr.endswith(".")]
        return LanguageAbbreviationData(
            replace_all=True,
            compound_abbr_regex=None,
            prepositive_regex=None,
            number_abbr_regex=None,
            standard_abbr_regex=None,
            standard_abbr_set=frozenset[str](),
            replace_all_dot_regex=build_replace_all_dot_regex(non_dot),
            replace_all_exact_regex=build_replace_all_exact_regex(all_abbr_clean),
            sentence_boundary_starters_regex=boundary_starters_regex,
        )

    all_raw = abbreviations | prepositive | number_abbr
    compound_list = sorted(
        {
            abbr.strip()
            for abbr in all_raw
            if ("." in abbr or " " in abbr) and abbr.strip()
        },
        key=len,
        reverse=True,
    )
    compound_abbr_regex: re.Pattern[str] | None = build_compound_abbr_regex(
        compound_list
    )

    compound_set = {abbr.lower().strip() for abbr in compound_list}

    prep_clean = sorted(
        [
            abbr.strip()
            for abbr in prepositive
            if abbr.strip() and abbr.lower().strip() not in compound_set
        ],
        key=len,
        reverse=True,
    )
    prepositive_regex: re.Pattern[str] | None = build_prepositive_abbr_regex(prep_clean)

    num_clean = sorted(
        [
            abbr.strip()
            for abbr in number_abbr
            if abbr.strip() and abbr.lower().strip() not in compound_set
        ],
        key=len,
        reverse=True,
    )
    number_abbr_regex: re.Pattern[str] | None = build_number_abbr_regex(num_clean)

    std_source = abbreviations if abbreviations else STANDARD_ABBREVIATIONS
    std_clean = sorted(
        [
            abbr.strip()
            for abbr in std_source
            if abbr.strip() and abbr.lower().strip() not in compound_set
        ],
        key=len,
        reverse=True,
    )

    standard_abbr_set: frozenset[str] = frozenset(abbr.lower() for abbr in std_clean)

    return LanguageAbbreviationData(
        replace_all=False,
        compound_abbr_regex=compound_abbr_regex,
        prepositive_regex=prepositive_regex,
        number_abbr_regex=number_abbr_regex,
        standard_abbr_regex=None,
        standard_abbr_set=standard_abbr_set,
        replace_all_dot_regex=None,
        replace_all_exact_regex=None,
        sentence_boundary_starters_regex=boundary_starters_regex,
    )


def replace_multi_period_abbreviations(
    text: str, config: LanguageProtocol | None = None
) -> str:
    """Mask all periods inside multi-period acronyms and abbreviations.

    Args:
        text: The source text string.
        config: Optional language configuration module.

    Returns:
        The text with all periods in multi-period abbreviations masked.
    """
    lang_module = config
    mpa_pattern = (
        lang_module.multi_period_abbreviation_regex if lang_module is not None else None
    )
    pattern = mpa_pattern if mpa_pattern is not None else MULTI_PERIOD_DEFAULT_REGEX
    return pattern.sub(lambda m: m.group(0).replace(".", PUA_PERIOD), text)


def search_for_abbreviations_in_string(
    text: str,
    config: LanguageProtocol | None = None,
) -> str:
    """Scan string against all abbreviation sets defined in language configuration.

    Args:
        text: The source text string.
        config: Optional language configuration module.

    Returns:
        The text with all identified abbreviations masked.
    """
    if not text:
        return text

    data = get_language_abbreviation_data(config)
    if data.replace_all:
        if data.replace_all_dot_regex:
            text = data.replace_all_dot_regex.sub(
                lambda m: m.group(1).replace(".", PUA_PERIOD) + PUA_PERIOD,
                text,
            )
        if data.replace_all_exact_regex:
            text = data.replace_all_exact_regex.sub(
                lambda m: m.group(1).replace(".", PUA_PERIOD),
                text,
            )
        return text

    if data.compound_abbr_regex:
        text = data.compound_abbr_regex.sub(
            lambda m: m.group(0).replace(".", PUA_PERIOD), text
        )
    if data.prepositive_regex:
        text = data.prepositive_regex.sub(r"\g<1>" + PUA_PERIOD, text)
    if data.number_abbr_regex:
        text = data.number_abbr_regex.sub(r"\g<1>" + PUA_PERIOD, text)
    if data.standard_abbr_regex:
        text = data.standard_abbr_regex.sub(
            lambda m: m.group(0).replace(".", PUA_PERIOD), text
        )

    if data.standard_abbr_set:

        def _replace_scan(match: re.Match[str]) -> str:
            word = match.group("word")
            if word.lower() in data.standard_abbr_set:
                lead = match.group("lead_uni") or ""
                trail = match.group("trail_uni") or ""
                return f"{word}{lead}{PUA_PERIOD}{trail}"
            return match.group(0)

        text = STANDARD_ABBR_SCAN_REGEX.sub(_replace_scan, text)

    return text


def replace_abbreviation_as_sentence_boundary(
    text: str,
    config: LanguageProtocol | None = None,
) -> str:
    """Restore terminal periods when an acronym is followed by a known sentence starter.

    Args:
        text: The source text string.
        config: Optional language configuration protocol.

    Returns:
        The text with sentence-terminal abbreviation periods unmasked.
    """
    data = get_language_abbreviation_data(config)
    if data.sentence_boundary_starters_regex is not None:
        text = data.sentence_boundary_starters_regex.sub(r"\g<1>.", text)
    return text


def replace_abbreviations(
    text: str,
    config: LanguageProtocol | None = None,
) -> str:
    """Execute complete abbreviation masking pipeline across all linguistic categories.

    Args:
        text: The source text string to process.
        config: Optional language configuration protocol.

    Returns:
        The text with all recognized abbreviation periods masked to PUA sentinels.
    """
    if not text:
        return text

    text = POSSESSIVE_ABBR_REGEX.sub(PUA_PERIOD, text)
    text = KOMMANDITGESELLSCHAFT_REGEX.sub(PUA_PERIOD, text)
    text = SINGLE_UPPERCASE_LETTER_REGEX.sub(
        lambda m: m.group(1).replace(".", PUA_PERIOD), text
    )
    text = replace_multi_period_abbreviations(text, config=config)
    text = search_for_abbreviations_in_string(text, config=config)
    text = SINGLE_LOWERCASE_LETTER_REGEX.sub(r"\g<1>" + PUA_PERIOD, text)

    for rule in AM_PM_RULES:
        text = rule.pattern.sub(rule.replacement, text)

    text = replace_abbreviation_as_sentence_boundary(text, config=config)
    return text
