"""Processing Pipeline Orchestrator for Sentence Boundary Disambiguation."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from functools import lru_cache
from types import ModuleType

from pragmatic_sbd.lang import LanguageConfig, get_language_module
from pragmatic_sbd.lang.common import (
    ALPHA_LIST_REGEX,
    AM_PM_RULES,
    BETWEEN_SINGLE_QUOTES_REGEX,
    COMMON_RULES,
    CONTINUOUS_PUNCTUATION_REGEX,
    DOUBLE_PUNCTUATION_RULES,
    ELLIPSIS_RULES,
    KOMMANDITGESELLSCHAFT_REGEX,
    LATIN_NUMERALS,
    MULTI_PERIOD_DEFAULT_REGEX,
    NUMBER_LIST_REGEX,
    NUMBER_RULES,
    NUMBERED_REFERENCE_REGEX,
    PARENS_BETWEEN_DOUBLE_QUOTES_REGEX,
    POSSESSIVE_ABBR_REGEX,
    PUA_DOUBLE_EE,
    PUA_DOUBLE_EQ,
    PUA_DOUBLE_QE,
    PUA_DOUBLE_QQ,
    PUA_EXCLAMATION,
    PUA_LEFT_PAREN,
    PUA_NEWLINE,
    PUA_PERIOD,
    PUA_QUESTION,
    PUA_RIGHT_PAREN,
    PUA_TEMP_END_PUNCT,
    PUNCTUATIONS,
    QUOTATION_AT_END_OF_SENTENCE_REGEX,
    ROMAN_DELIM_REGEX,
    ROMAN_NUMERALS,
    ROMAN_NUMERALS_SET,
    ROMAN_PARENS_REGEX,
    SENTENCE_BOUNDARY_REGEX,
    SINGLE_LOWERCASE_LETTER_REGEX,
    SINGLE_UPPERCASE_LETTER_REGEX,
    SPLIT_SPACE_QUOTATION_AT_END_OF_SENTENCE_REGEX,
    STANDARD_PAIRED_PATTERNS,
    WORD_WITH_LEADING_APOSTROPHE,
    Rule,
    mask_exclamation_words,
    mask_punctuation,
    mask_single_quote_punctuation,
    unmask_all,
)

LINE_SPLIT_REGEX = re.compile(rf"(?:\r\n|\r|\n|{PUA_NEWLINE})")

_BULLET_CHARS: frozenset[str] = frozenset({"•", "⁃"})
_LEAD_WHITESPACE: frozenset[str] = frozenset({" ", "\t"})
_PUA_SEARCH_PUNCTUATIONS: frozenset[str] = frozenset(
    {
        PUA_PERIOD,
        PUA_EXCLAMATION,
        PUA_QUESTION,
        PUA_DOUBLE_QE,
        PUA_DOUBLE_EQ,
        PUA_DOUBLE_QQ,
        PUA_DOUBLE_EE,
        PUA_TEMP_END_PUNCT,
    }
)


# =============================================================================
# 1. List Item Masking
# =============================================================================


def _apply_replacements(text: str, replacements: dict[int, str]) -> str:
    """Efficiently assemble a modified string from sparse character replacements.

    Args:
        text: The original text.
        replacements: A map from character index to replacement string.

    Returns:
        The new string with all replacements applied.
    """
    if not replacements:
        return text
    result: list[str] = []
    last_idx = 0
    for idx in sorted(replacements.keys()):
        result.append(text[last_idx:idx])
        result.append(replacements[idx])
        last_idx = idx + 1
    result.append(text[last_idx:])
    return "".join(result)


def _mask_numbered_lists(text: str) -> str:
    """Mask periods and insert breaks for numbered list items.

    Args:
        text: The text string to process.

    Returns:
        The text with numbered list delimiters masked.
    """
    matches = list(NUMBER_LIST_REGEX.finditer(text))
    if not matches:
        return text

    items: list[tuple[int, bool, int, int, str, int, int, int, int, bool]] = []
    for match in matches:
        leading_chars = match.group("lead") or ""
        match_start, match_end = match.span()
        has_bullet = any(bullet in leading_chars for bullet in _BULLET_CHARS)

        leading_space_index = -1
        if leading_chars and leading_chars[0] in _LEAD_WHITESPACE and match_start > 0:
            leading_space_index = match_start

        if match.group("num_p") is not None:
            item_value = int(match.group("num_p"))
            lparen_index = match.start("lparen")
            rparen_index = match_end - 1
            items.append(
                (
                    item_value,
                    True,
                    match_start,
                    match_end,
                    "",
                    -1,
                    lparen_index,
                    rparen_index,
                    leading_space_index,
                    has_bullet,
                )
            )
        else:
            item_value = int(match.group("num"))
            delimiter = match.group("delim") or ""
            delimiter_start = match.start("delim")
            items.append(
                (
                    item_value,
                    False,
                    match_start,
                    match_end,
                    delimiter,
                    delimiter_start,
                    -1,
                    -1,
                    leading_space_index,
                    has_bullet,
                )
            )

    is_list_item: list[bool] = [False] * len(items)
    for index, (item_value, _, match_start, _, _, _, _, _, _, has_bullet) in enumerate(items):
        if has_bullet:
            is_list_item[index] = True
        elif index + 1 < len(items) and items[index + 1][0] == item_value + 1:
            is_list_item[index] = True
            is_list_item[index + 1] = True
        elif (
            index > 0
            and (
                items[index - 1][0] == item_value - 1
                or (items[index - 1][0] == 9 and item_value == 0)
                or (items[index - 1][0] == 0 and item_value == 9)
            )
        ) or (item_value == 1 and (match_start == 0 or text[match_start - 1] in ("\n", "\r"))):
            is_list_item[index] = True

    if not any(is_list_item):
        return text

    replacements: dict[int, str] = {}
    for index, is_valid in enumerate(is_list_item):
        if not is_valid:
            continue
        (
            _,
            is_parens,
            _,
            _,
            delimiter,
            delimiter_start,
            lparen_index,
            rparen_index,
            leading_space_index,
            _,
        ) = items[index]

        if is_parens:
            if lparen_index >= 0 and text[lparen_index] == "(":
                replacements[lparen_index] = PUA_LEFT_PAREN
            if rparen_index >= 0 and text[rparen_index] == ")":
                replacements[rparen_index] = PUA_RIGHT_PAREN
        else:
            dot_offset = delimiter.find(".")
            if dot_offset >= 0:
                replacements[delimiter_start + dot_offset] = PUA_PERIOD

        if leading_space_index >= 0 and text[leading_space_index] == " ":
            preceding_str = text[max(0, leading_space_index - 4) : leading_space_index]
            if not preceding_str.lower().endswith("for"):
                replacements[leading_space_index] = "\r"

    return _apply_replacements(text, replacements)


def _mask_alphabetical_lists(text: str) -> str:
    """Mask periods and insert breaks for alphabetical list items.

    Args:
        text: The text string to process.

    Returns:
        The text with alphabetical list delimiters masked.
    """
    matches = list(ALPHA_LIST_REGEX.finditer(text))
    if not matches:
        return text

    items: list[tuple[str, bool, int, int, str, int, int, int, int, bool]] = []
    for match in matches:
        leading_chars = match.group("lead") or ""
        match_start, match_end = match.span()
        has_bullet = any(bullet in leading_chars for bullet in _BULLET_CHARS)

        leading_space_index = -1
        if leading_chars and leading_chars[0] in _LEAD_WHITESPACE and match_start > 0:
            leading_space_index = match_start

        if match.group("letter_p") is not None:
            letter = match.group("letter_p").lower()
            lparen_index = match.start("lparen")
            rparen_index = match_end - 1
            items.append(
                (
                    letter,
                    True,
                    match_start,
                    match_end,
                    "",
                    -1,
                    lparen_index,
                    rparen_index,
                    leading_space_index,
                    has_bullet,
                )
            )
        else:
            letter = match.group("letter").lower()
            delimiter = match.group("delim") or ""
            delimiter_start = match.start("delim")
            items.append(
                (
                    letter,
                    False,
                    match_start,
                    match_end,
                    delimiter,
                    delimiter_start,
                    -1,
                    -1,
                    leading_space_index,
                    has_bullet,
                )
            )

    is_list_item: list[bool] = [False] * len(items)
    for index, (letter, _, _, _, _, _, _, _, _, has_bullet) in enumerate(items):
        current_index = LATIN_NUMERALS.get(letter, -1)
        if current_index < 0:
            continue

        if has_bullet:
            is_list_item[index] = True
        if index + 1 < len(items):
            next_letter = items[index + 1][0]
            next_index = LATIN_NUMERALS.get(next_letter, -1)
            if next_index == current_index + 1:
                is_list_item[index] = True
                is_list_item[index + 1] = True
        if index > 0:
            previous_letter = items[index - 1][0]
            previous_index = LATIN_NUMERALS.get(previous_letter, -1)
            if previous_index == current_index - 1:
                is_list_item[index] = True

    if not any(is_list_item):
        return text

    replacements: dict[int, str] = {}
    for index, is_valid in enumerate(is_list_item):
        if not is_valid:
            continue
        (
            _,
            is_parens,
            _,
            _,
            delimiter,
            delimiter_start,
            lparen_index,
            rparen_index,
            leading_space_index,
            _,
        ) = items[index]

        if is_parens:
            if lparen_index >= 0 and text[lparen_index] == "(":
                replacements[lparen_index] = PUA_LEFT_PAREN
            if rparen_index >= 0 and text[rparen_index] == ")":
                replacements[rparen_index] = PUA_RIGHT_PAREN
        else:
            dot_offset = delimiter.find(".")
            if dot_offset >= 0:
                replacements[delimiter_start + dot_offset] = PUA_PERIOD

        if leading_space_index >= 0 and text[leading_space_index] == " ":
            replacements[leading_space_index] = "\r"

    return _apply_replacements(text, replacements)


def _mask_parenthesized_and_roman_lists(text: str) -> str:
    """Mask parens and delimiters in Roman numeral list items like (i), (ii), i., ii.).

    Args:
        text: The text string to process.

    Returns:
        The text with Roman numeral list markers masked.
    """
    roman_parens_matches = list(ROMAN_PARENS_REGEX.finditer(text))
    roman_delim_matches = list(ROMAN_DELIM_REGEX.finditer(text))
    if not roman_parens_matches and not roman_delim_matches:
        return text

    replacements: dict[int, str] = {}

    if roman_parens_matches:
        roman_paren_items: list[tuple[str, int, int, int, int, int]] = []
        for match in roman_parens_matches:
            roman = match.group("roman").lower()
            leading_chars = match.group("lead") or ""
            match_start, match_end = match.span()
            roman_start = match.start("roman")

            if roman in ROMAN_NUMERALS_SET:
                leading_space_index = -1
                if leading_chars and leading_chars[0] in _LEAD_WHITESPACE and match_start > 0:
                    leading_space_index = match_start
                lparen_index = roman_start - 1
                rparen_index = match_end - 1
                roman_paren_items.append(
                    (
                        roman,
                        match_start,
                        match_end,
                        lparen_index,
                        rparen_index,
                        leading_space_index,
                    )
                )

        is_valid_roman_paren: list[bool] = [False] * len(roman_paren_items)
        for index, (roman, match_start, match_end, _, _, _) in enumerate(roman_paren_items):
            current_index = ROMAN_NUMERALS[roman]
            if index + 1 < len(roman_paren_items):
                next_roman = roman_paren_items[index + 1][0]
                next_index = ROMAN_NUMERALS[next_roman]
                if next_index == current_index + 1:
                    is_valid_roman_paren[index] = True
                    is_valid_roman_paren[index + 1] = True
            if index > 0:
                previous_roman = roman_paren_items[index - 1][0]
                previous_index = ROMAN_NUMERALS[previous_roman]
                if previous_index == current_index - 1:
                    is_valid_roman_paren[index] = True
            elif (
                match_start == 0
                or text[match_start - 1] in ("\n", "\r")
                or (match_end < len(text) and bool(re.match(r"\s+[A-Z]", text[match_end:])))
            ):
                is_valid_roman_paren[index] = True

        for index, is_valid in enumerate(is_valid_roman_paren):
            if not is_valid:
                continue
            _, _, _, lparen_index, rparen_index, leading_space_index = roman_paren_items[index]
            if lparen_index >= 0 and text[lparen_index] == "(":
                replacements[lparen_index] = PUA_LEFT_PAREN
            if rparen_index >= 0 and text[rparen_index] == ")":
                replacements[rparen_index] = PUA_RIGHT_PAREN
            if leading_space_index >= 0 and text[leading_space_index] == " ":
                replacements[leading_space_index] = "\r"

    if roman_delim_matches:
        roman_delim_items: list[tuple[str, int, int, str, int, int]] = []
        for match in roman_delim_matches:
            roman = match.group("roman").lower()
            leading_chars = match.group("lead") or ""
            delimiter = match.group("delim") or ""
            match_start, match_end = match.span()
            delimiter_start = match.start("delim")

            if roman in ROMAN_NUMERALS_SET:
                leading_space_index = -1
                if leading_chars and leading_chars[0] in _LEAD_WHITESPACE and match_start > 0:
                    leading_space_index = match_start
                roman_delim_items.append(
                    (
                        roman,
                        match_start,
                        match_end,
                        delimiter,
                        delimiter_start,
                        leading_space_index,
                    )
                )

        is_valid_roman_delim: list[bool] = [False] * len(roman_delim_items)
        for index, (roman, match_start, _, _, _, _) in enumerate(roman_delim_items):
            current_index = ROMAN_NUMERALS[roman]
            if index + 1 < len(roman_delim_items):
                next_roman = roman_delim_items[index + 1][0]
                next_index = ROMAN_NUMERALS[next_roman]
                if next_index == current_index + 1:
                    is_valid_roman_delim[index] = True
                    is_valid_roman_delim[index + 1] = True
            if index > 0:
                previous_roman = roman_delim_items[index - 1][0]
                previous_index = ROMAN_NUMERALS[previous_roman]
                if previous_index == current_index - 1:
                    is_valid_roman_delim[index] = True
            elif current_index == 0 and (match_start == 0 or text[match_start - 1] in ("\n", "\r")):
                is_valid_roman_delim[index] = True

        for index, is_valid in enumerate(is_valid_roman_delim):
            if not is_valid:
                continue
            _, _, _, delimiter, delimiter_start, leading_space_index = roman_delim_items[index]

            dot_offset = delimiter.find(".")
            if dot_offset >= 0:
                replacements[delimiter_start + dot_offset] = PUA_PERIOD

            if leading_space_index >= 0 and text[leading_space_index] == " ":
                replacements[leading_space_index] = "\r"

    return _apply_replacements(text, replacements)


def mask_list_items(text: str, lang: str = "") -> str:
    """Mask list item periods and delimiters with PUA sentinels.

    Args:
        text: The text string containing lists.
        lang: Two-letter ISO language code. Defaults to "".

    Returns:
        The text with all detected list delimiters masked.
    """
    if not text:
        return text

    supports_alpha: bool = True

    if "•" in text or "⁃" in text:
        text = re.sub(r"(?<=\S)\s(?=[•⁃])", "\r", text)
    text = _mask_parenthesized_and_roman_lists(text)
    text = _mask_numbered_lists(text)
    if supports_alpha:
        text = _mask_alphabetical_lists(text)
    return text


# =============================================================================
# 2. Abbreviation Disambiguation
# =============================================================================


PARENS_LEAD_SPACE_REGEX: re.Pattern[str] = re.compile(r"\s(?=\()")
PARENS_TRAIL_SPACE_REGEX: re.Pattern[str] = re.compile(r"(?<=\))\s")


@dataclass(slots=True, frozen=True)
class LanguageAbbreviationData:
    """Pre-compiled and cached regex patterns for language-specific abbreviation handling."""

    replace_all: bool
    compound_abbr_regex: re.Pattern[str] | None
    prepositive_regex: re.Pattern[str] | None
    number_abbr_regex: re.Pattern[str] | None
    standard_abbr_regex: re.Pattern[str] | None
    replace_all_dot_regex: re.Pattern[str] | None
    replace_all_exact_regex: re.Pattern[str] | None
    sentence_boundary_starters_regex: re.Pattern[str] | None


@lru_cache(maxsize=32)
def get_language_abbreviation_data(lang: str) -> LanguageAbbreviationData:
    """Pre-compile and cache unified category regexes per language.

    Args:
        lang: Two-letter ISO language code.

    Returns:
        The pre-compiled abbreviation patterns for the language.
    """
    lang_module = get_language_module(lang) if lang else None
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

    boundary_starters_regex: re.Pattern[str] | None = None
    if sentence_starters:
        starters_pattern = "|".join(
            re.escape(word) for word in sorted(sentence_starters, key=len, reverse=True)
        )
        boundary_starters_regex = re.compile(
            rf"((?:U{PUA_PERIOD}S|U\.S|U{PUA_PERIOD}K|E{PUA_PERIOD}U|E\.U|"
            rf"U{PUA_PERIOD}S{PUA_PERIOD}A|U\.S\.A|I|i{PUA_PERIOD}v|I{PUA_PERIOD}V|i\.v|I\.V))"
            rf"{PUA_PERIOD}(?=\s+(?:{starters_pattern})\b)"
        )

    if replace_all:
        all_abbr_clean = sorted(
            {abbr.strip() for abbr in (abbreviations | prepositive | number_abbr) if abbr.strip()},
            key=len,
            reverse=True,
        )
        non_dot = [abbr for abbr in all_abbr_clean if not abbr.endswith(".")]
        dot_regex: re.Pattern[str] | None = None
        if non_dot:
            dot_regex = re.compile(
                rf"((?:(?<=^)|(?<=\s))(?i:{'|'.join(re.escape(abbr) for abbr in non_dot)}))\."
            )
        exact_regex: re.Pattern[str] | None = None
        if all_abbr_clean:
            exact_regex = re.compile(
                rf"((?:(?<=^)|(?<=\s))(?i:{'|'.join(re.escape(abbr) for abbr in all_abbr_clean)}))(?=(\s|$|[.:\-?,!\"\'“”«»]))"
            )
        return LanguageAbbreviationData(
            replace_all=True,
            compound_abbr_regex=None,
            prepositive_regex=None,
            number_abbr_regex=None,
            standard_abbr_regex=None,
            replace_all_dot_regex=dot_regex,
            replace_all_exact_regex=exact_regex,
            sentence_boundary_starters_regex=boundary_starters_regex,
        )

    all_raw = abbreviations | prepositive | number_abbr
    compound_list = sorted(
        {abbr.strip() for abbr in all_raw if ("." in abbr or " " in abbr) and abbr.strip()},
        key=len,
        reverse=True,
    )
    compound_abbr_regex: re.Pattern[str] | None = None
    if compound_list:
        compound_pattern = "|".join(re.escape(abbr) for abbr in compound_list)
        compound_abbr_regex = re.compile(
            rf"((?:(?<=^)|(?<=\s))(?i:{compound_pattern}))"
            r"[\u200e\u200f\u202a-\u202e\u2066-\u2069]*\.?[\u200e\u200f\u202a-\u202e\u2066-\u2069]*"
            rf"(?=[.:\-?,!\"\'“”«»]|\s+(?:[a-zа-яё\u0600-\u06ff]|I\s|I'm|I'll|\d|\(|\"|'|«|„))"
        )

    compound_set = {abbr.lower().strip() for abbr in compound_list}

    prep_clean = sorted(
        [abbr.strip() for abbr in prepositive if abbr.strip() and abbr.lower().strip() not in compound_set],
        key=len,
        reverse=True,
    )
    prepositive_regex: re.Pattern[str] | None = None
    if prep_clean:
        prep_pattern = "|".join(re.escape(abbr) for abbr in prep_clean)
        prepositive_regex = re.compile(rf"((?:(?<=^)|(?<=\s))(?i:{prep_pattern}))\.(?=(\s|:\d+))")

    num_clean = sorted(
        [abbr.strip() for abbr in number_abbr if abbr.strip() and abbr.lower().strip() not in compound_set],
        key=len,
        reverse=True,
    )
    number_abbr_regex: re.Pattern[str] | None = None
    if num_clean:
        num_pattern = "|".join(re.escape(abbr) for abbr in num_clean)
        number_abbr_regex = re.compile(rf"((?:(?<=^)|(?<=\s))(?i:{num_pattern}))\.(?=(\s*\d|\s+\())")

    prep_set = {abbr.lower().strip() for abbr in prepositive if abbr.strip()}
    num_set = {abbr.lower().strip() for abbr in number_abbr if abbr.strip()} - prep_set
    std_clean = sorted(
        {
            abbr.strip()
            for abbr in abbreviations
            if abbr.strip()
            and abbr.lower().strip() not in compound_set
            and abbr.lower().strip() not in prep_set
            and abbr.lower().strip() not in num_set
        },
        key=len,
        reverse=True,
    )
    standard_abbr_regex: re.Pattern[str] | None = None
    if std_clean:
        std_pattern = "|".join(re.escape(abbr) for abbr in std_clean)
        standard_abbr_regex = re.compile(
            rf"((?:(?<=^)|(?<=\s))(?i:{std_pattern}))"
            r"[\u200e\u200f\u202a-\u202e\u2066-\u2069]*\."
            r"[\u200e\u200f\u202a-\u202e\u2066-\u2069]*"
            rf"(?=[.:\-?,!\"\'“”«»]|\s+(?:[a-zа-яё\u0600-\u06ff]|I\s|I'm|I'll|\d|\(|\"|'|«|„))"
        )

    return LanguageAbbreviationData(
        replace_all=False,
        compound_abbr_regex=compound_abbr_regex,
        prepositive_regex=prepositive_regex,
        number_abbr_regex=number_abbr_regex,
        standard_abbr_regex=standard_abbr_regex,
        replace_all_dot_regex=None,
        replace_all_exact_regex=None,
        sentence_boundary_starters_regex=boundary_starters_regex,
    )


def replace_pre_number_abbr(text: str, abbr: str) -> str:
    """Mask periods in number-preceding abbreviations (e.g. 'No. 5', 'pp. (1-3)').

    Args:
        text: The input text.
        abbr: The abbreviation string.

    Returns:
        The text with matching abbreviation periods masked.
    """
    escaped_abbr = re.escape(abbr.strip())
    pattern = rf"((?:(?<=^)|(?<=\s))(?i:{escaped_abbr}))\.(?=(\s*\d|\s+\())"
    return re.sub(pattern, r"\g<1>" + PUA_PERIOD, text)


def replace_prepositive_abbr(text: str, abbr: str) -> str:
    """Mask periods in prepositive titles and honorifics (e.g. 'Mr. Jones', 'Gen. 1:1').

    Args:
        text: The input text.
        abbr: The abbreviation string.

    Returns:
        The text with matching prepositive periods masked.
    """
    escaped_abbr = re.escape(abbr.strip())
    pattern = rf"((?:(?<=^)|(?<=\s))(?i:{escaped_abbr}))\.(?=(\s|:\d+))"
    return re.sub(pattern, r"\g<1>" + PUA_PERIOD, text)


def replace_period_of_abbr(text: str, abbr: str) -> str:
    """Mask standard abbreviation periods when followed by lowercase text, numbers, or punctuation.

    Args:
        text: The input text string.
        abbr: The abbreviation string to target.

    Returns:
        The text with targeted abbreviation periods replaced by sentinels.
    """
    escaped_abbr = re.escape(abbr.strip())
    pattern = (
        rf"((?:(?<=^)|(?<=\s))(?i:{escaped_abbr}))"
        r"[\u200e\u200f\u202a-\u202e\u2066-\u2069]*\."
        r"[\u200e\u200f\u202a-\u202e\u2066-\u2069]*"
        rf"(?=[.:\-?,!\"\'“”«»]|\s+(?:[a-zа-яё\u0600-\u06ff]|I\s|I'm|I'll|\d|\(|\"|'|«|„))"
    )
    return re.sub(pattern, lambda m: m.group(0).replace(".", PUA_PERIOD), text)


def replace_multi_period_abbreviations(text: str, lang: str = "") -> str:
    """Mask all periods inside multi-period acronyms and abbreviations.

    Args:
        text: The input text string.
        lang: Two-letter ISO language code. Defaults to "".

    Returns:
        The text with all periods in multi-period abbreviations masked.
    """
    lang_module = get_language_module(lang) if lang else None
    mpa_pattern = lang_module.multi_period_abbreviation_regex if lang_module is not None else None
    pattern = mpa_pattern if mpa_pattern is not None else MULTI_PERIOD_DEFAULT_REGEX
    return pattern.sub(lambda m: m.group(0).replace(".", PUA_PERIOD), text)


def replace_abbreviation_as_sentence_boundary(text: str, lang: str = "") -> str:
    """Restore terminal periods when an acronym is followed by a known sentence starter.

    Args:
        text: The input text string.
        lang: Two-letter ISO language code. Defaults to "".

    Returns:
        The text with proper periods restored at sentence boundaries.
    """
    data = get_language_abbreviation_data(lang)
    if data.sentence_boundary_starters_regex:
        return data.sentence_boundary_starters_regex.sub(r"\g<1>.", text)
    return text


def search_for_abbreviations_in_string(text: str, lang: str = "") -> str:
    """Scan string against all abbreviation sets defined in language configuration.

    Args:
        text: The input text string.
        lang: Two-letter ISO language code. Defaults to "".

    Returns:
        The text with all identified abbreviations masked.
    """
    if not text:
        return text

    data = get_language_abbreviation_data(lang)
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
        text = data.compound_abbr_regex.sub(lambda m: m.group(0).replace(".", PUA_PERIOD), text)
    if data.prepositive_regex:
        text = data.prepositive_regex.sub(r"\g<1>" + PUA_PERIOD, text)
    if data.number_abbr_regex:
        text = data.number_abbr_regex.sub(r"\g<1>" + PUA_PERIOD, text)
    if data.standard_abbr_regex:
        text = data.standard_abbr_regex.sub(lambda m: m.group(0).replace(".", PUA_PERIOD), text)

    return text


def replace_abbreviations(text: str, lang: str = "") -> str:
    """Disambiguate and mask abbreviations within text.

    Args:
        text: The input text string.
        lang: Two-letter ISO language code. Defaults to "".

    Returns:
        The text with all abbreviation periods masked.
    """
    if not text:
        return text

    text = POSSESSIVE_ABBR_REGEX.sub(PUA_PERIOD, text)
    text = KOMMANDITGESELLSCHAFT_REGEX.sub(PUA_PERIOD, text)
    for _ in range(3):
        text = SINGLE_UPPERCASE_LETTER_REGEX.sub(r"\g<1>" + PUA_PERIOD, text)

    text = replace_multi_period_abbreviations(text, lang=lang)

    lang_module = get_language_module(lang) if lang else None
    lang_rules: tuple[Rule, ...] = lang_module.rules if lang_module is not None else ()
    for rule in lang_rules:
        text = rule.pattern.sub(rule.replacement, text)

    text = search_for_abbreviations_in_string(text, lang=lang)

    text = SINGLE_LOWERCASE_LETTER_REGEX.sub(r"\g<1>" + PUA_PERIOD, text)

    for rule in AM_PM_RULES:
        text = rule.pattern.sub(rule.replacement, text)

    text = replace_abbreviation_as_sentence_boundary(text, lang=lang)
    return text


# =============================================================================
# 3. Paired Punctuation Masking
# =============================================================================


def mask_between_punctuation(text: str, lang: str = "") -> str:
    """Mask punctuation enclosed within paired quotes, brackets, parens, and dashes.

    Args:
        text: The input text string.
        lang: Two-letter ISO language code. Defaults to "".

    Returns:
        The text with punctuation inside quotes or brackets masked.
    """
    if not text:
        return text

    if not (WORD_WITH_LEADING_APOSTROPHE.search(text) and not re.search(r"'\s", text)):
        text = BETWEEN_SINGLE_QUOTES_REGEX.sub(mask_single_quote_punctuation, text)

    for pattern, handler in STANDARD_PAIRED_PATTERNS:
        text = pattern.sub(handler, text)

    lang_module = get_language_module(lang) if lang else None
    lang_paired_patterns: tuple[re.Pattern[str], ...] = (
        lang_module.paired_punctuation_patterns if lang_module is not None else ()
    )
    for custom_pattern in lang_paired_patterns:
        text = custom_pattern.sub(mask_punctuation, text)

    return text


# =============================================================================
# 4. Disambiguator Core Pipeline
# =============================================================================


@dataclass(slots=True)
class Disambiguator:
    """Orchestrates sentence boundary disambiguation and segmentation.

    Args:
        text: The text string to disambiguate. Defaults to "".
        lang: Two-letter ISO language code or pre-loaded module/config. Defaults to "".
        char_span: If True, tracks character spans. Defaults to False.
    """

    text: str = ""
    lang: str | ModuleType | LanguageConfig = ""
    char_span: bool = False
    lang_module: LanguageConfig | None = field(init=False, default=None)
    lang_code: str = field(init=False, default="")

    def __post_init__(self) -> None:
        self.text = self.text or ""
        self.lang_module = get_language_module(self.lang) if self.lang else None
        if isinstance(self.lang, str):
            self.lang_code = self.lang
        elif self.lang_module:
            self.lang_code = self.lang_module.iso_code
        else:
            self.lang_code = ""

    def disambiguate(self) -> list[str]:
        """Execute the full 1:1 length-preserving disambiguation and extraction pipeline.

        Returns:
            A list of segmented sentence strings.
        """
        if not self.text:
            return []

        text = self.text

        # 1. Lists: Mask list numbers and format markers
        text = mask_list_items(text, lang=self.lang_code)

        # 2. Abbreviations: Mask periods in honorifics, initials, acronyms
        text = replace_abbreviations(text, lang=self.lang_code)

        # 3. Numbers & Dates: Mask decimals, versions, timestamps
        text = self._mask_numbers_and_dates(text)

        # 4. Exclamation words: Mask internal exclamation marks (e.g., 'Yahoo!')
        text = mask_exclamation_words(text)

        # 5. Paired punctuation: Mask enclosed periods/punctuation
        text = self._check_for_parens_between_quotes(text)
        text = mask_between_punctuation(text, lang=self.lang_code)

        # 6. Continuous & Common punctuation
        text = self._mask_continuous_punctuation(text)
        for rule in COMMON_RULES:
            text = rule.pattern.sub(rule.replacement, text)

        # 7. Boundary splitting
        return self._split_into_segments(text)

    def _check_for_parens_between_quotes(self, text: str) -> str:
        """Insert break delimiters around parenthetical citations between double quotes.

        Args:
            text: The text string to process.

        Returns:
            The text with breaks around parentheticals.
        """

        def _paren_replace(match: re.Match[str]) -> str:
            matched_text = match.group(0)
            leading_space_replaced = PARENS_LEAD_SPACE_REGEX.sub("\r", matched_text)
            return PARENS_TRAIL_SPACE_REGEX.sub("\r", leading_space_replaced)

        return PARENS_BETWEEN_DOUBLE_QUOTES_REGEX.sub(_paren_replace, text)

    def _mask_numbers_and_dates(self, text: str) -> str:
        """Mask periods in decimal numbers, timestamps, and date formats.

        Args:
            text: The text string to process.

        Returns:
            The text with number/date periods masked.
        """
        for rule in NUMBER_RULES:
            text = rule.pattern.sub(rule.replacement, text)

        def _ref_sub(match: re.Match[str]) -> str:
            reference = match.group("ref")
            trailing_space = match.group("space") or ""
            if match.end() == len(match.string):
                return f"{PUA_PERIOD}{reference}"
            return f"{PUA_PERIOD}{reference}{trailing_space}\r"

        text = NUMBERED_REFERENCE_REGEX.sub(_ref_sub, text)

        if self.lang_module is not None:
            for rule in self.lang_module.rules:
                text = rule.pattern.sub(rule.replacement, text)

        return text

    def _mask_continuous_punctuation(self, text: str) -> str:
        """Mask double punctuation marks and multi-dot ellipses.

        Args:
            text: The text string to process.

        Returns:
            The text with contiguous punctuation masked.
        """

        def _cont_repl(match: re.Match[str]) -> str:
            return match.group(1).replace("!", PUA_EXCLAMATION).replace("?", PUA_QUESTION)

        text = CONTINUOUS_PUNCTUATION_REGEX.sub(_cont_repl, text)
        for rule in DOUBLE_PUNCTUATION_RULES:
            text = rule.pattern.sub(rule.replacement, text)
        for rule in ELLIPSIS_RULES:
            text = rule.pattern.sub(rule.replacement, text)
        return text

    def _split_into_segments(self, text: str) -> list[str]:
        """Split disambiguated text into sentence segments using boundary regex.

        Args:
            text: The fully masked text string.

        Returns:
            A list of final unmasked, trimmed sentence strings.
        """
        boundary_regex = (
            self.lang_module.sentence_boundary_regex
            if self.lang_module and self.lang_module.sentence_boundary_regex is not None
            else SENTENCE_BOUNDARY_REGEX
        )
        punctuations = (
            self.lang_module.punctuations
            if self.lang_module and self.lang_module.punctuations is not None
            else PUNCTUATIONS
        )

        search_punctuations = punctuations | _PUA_SEARCH_PUNCTUATIONS

        quote_regex = QUOTATION_AT_END_OF_SENTENCE_REGEX
        split_quote_regex = SPLIT_SPACE_QUOTATION_AT_END_OF_SENTENCE_REGEX

        segments: list[str] = []
        for line in LINE_SPLIT_REGEX.split(text):
            if not line:
                continue
            if not search_punctuations.isdisjoint(line):
                processed_line = line if line[-1] in punctuations else (line + PUA_TEMP_END_PUNCT)
                matches = list(boundary_regex.finditer(processed_line))
                if matches:
                    for match in matches:
                        matched_text = match.group(0)
                        if quote_regex.search(matched_text):
                            parts = split_quote_regex.split(matched_text)
                            segments.extend(unmask_all(part).strip() for part in parts if part.strip())
                        else:
                            cleaned_segment = unmask_all(matched_text).strip()
                            if cleaned_segment:
                                segments.append(cleaned_segment)
                else:
                    raw_line = unmask_all(line).strip()
                    if raw_line:
                        segments.append(raw_line)
            else:
                raw_line = unmask_all(line).strip()
                if raw_line:
                    segments.append(raw_line)

        return segments
