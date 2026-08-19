"""Processing Pipeline Orchestrator for Sentence Boundary Disambiguation."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, ClassVar

from pragmatic_sbd.lang import get_language_module
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

if TYPE_CHECKING:
    from types import ModuleType

LINE_SPLIT_REGEX = re.compile(rf"(?:\r\n|\r|\n|{PUA_NEWLINE})")


# =============================================================================
# 1. List Item Masking
# =============================================================================


def _mask_numbered_lists(text: str) -> str:
    """Mask periods and insert breaks for numbered list items."""
    matches = list(NUMBER_LIST_REGEX.finditer(text))
    if not matches:
        return text

    items: list[tuple[int, bool, int, int, str, int, int, int, int, bool]] = []
    for m in matches:
        lead = m.group("lead") or ""
        m_start, m_end = m.span()
        has_bullet = any(b in lead for b in ("•", "⁃"))

        lead_space_idx = -1
        if lead and lead[0] in (" ", "\t") and m_start > 0:
            lead_space_idx = m_start

        if m.group("num_p") is not None:
            val = int(m.group("num_p"))
            lparen_idx = m.start("lparen")
            rparen_idx = m_end - 1
            items.append(
                (val, True, m_start, m_end, "", -1, lparen_idx, rparen_idx, lead_space_idx, has_bullet)
            )
        else:
            val = int(m.group("num"))
            delim = m.group("delim") or ""
            delim_start = m.start("delim")
            items.append((val, False, m_start, m_end, delim, delim_start, -1, -1, lead_space_idx, has_bullet))

    is_list_item: list[bool] = [False] * len(items)
    for i, (val, _, m_start, _, _, _, _, _, _, has_bullet) in enumerate(items):
        if has_bullet:
            is_list_item[i] = True
        elif i + 1 < len(items) and items[i + 1][0] == val + 1:
            is_list_item[i] = True
            is_list_item[i + 1] = True
        elif (
            i > 0
            and (
                items[i - 1][0] == val - 1
                or (items[i - 1][0] == 9 and val == 0)
                or (items[i - 1][0] == 0 and val == 9)
            )
        ) or (val == 1 and (m_start == 0 or text[m_start - 1] in ("\n", "\r"))):
            is_list_item[i] = True

    chars = list(text)
    for i, is_valid in enumerate(is_list_item):
        if not is_valid:
            continue
        _, is_parens, _, _, delim, delim_start, lparen_idx, rparen_idx, lead_space_idx, _ = items[i]

        if is_parens:
            if lparen_idx >= 0 and chars[lparen_idx] == "(":
                chars[lparen_idx] = PUA_LEFT_PAREN
            if rparen_idx >= 0 and chars[rparen_idx] == ")":
                chars[rparen_idx] = PUA_RIGHT_PAREN
        elif "." in delim:
            dot_offset = delim.index(".")
            chars[delim_start + dot_offset] = PUA_PERIOD

        if lead_space_idx >= 0 and chars[lead_space_idx] == " ":
            preceding_str = "".join(chars[max(0, lead_space_idx - 4) : lead_space_idx])
            if not preceding_str.lower().endswith("for"):
                chars[lead_space_idx] = "\r"

    return "".join(chars)


def _mask_alphabetical_lists(text: str) -> str:
    """Mask periods and insert breaks for alphabetical list items."""
    matches = list(ALPHA_LIST_REGEX.finditer(text))
    if not matches:
        return text

    items: list[tuple[str, bool, int, int, str, int, int, int, int, bool]] = []
    for m in matches:
        lead = m.group("lead") or ""
        m_start, m_end = m.span()
        has_bullet = any(b in lead for b in ("•", "⁃"))

        lead_space_idx = -1
        if lead and lead[0] in (" ", "\t") and m_start > 0:
            lead_space_idx = m_start

        if m.group("letter_p") is not None:
            letter = m.group("letter_p").lower()
            lparen_idx = m.start("lparen")
            rparen_idx = m_end - 1
            items.append(
                (letter, True, m_start, m_end, "", -1, lparen_idx, rparen_idx, lead_space_idx, has_bullet)
            )
        else:
            letter = m.group("letter").lower()
            delim = m.group("delim") or ""
            delim_start = m.start("delim")
            items.append(
                (letter, False, m_start, m_end, delim, delim_start, -1, -1, lead_space_idx, has_bullet)
            )

    is_list_item: list[bool] = [False] * len(items)
    for i, (letter, _, _, _, _, _, _, _, _, has_bullet) in enumerate(items):
        curr_idx = LATIN_NUMERALS.index(letter) if letter in LATIN_NUMERALS else -1
        if curr_idx < 0:
            continue

        if has_bullet:
            is_list_item[i] = True
        if i + 1 < len(items):
            next_letter = items[i + 1][0]
            next_idx = LATIN_NUMERALS.index(next_letter) if next_letter in LATIN_NUMERALS else -1
            if next_idx == curr_idx + 1:
                is_list_item[i] = True
                is_list_item[i + 1] = True
        if i > 0:
            prev_letter = items[i - 1][0]
            prev_idx = LATIN_NUMERALS.index(prev_letter) if prev_letter in LATIN_NUMERALS else -1
            if prev_idx == curr_idx - 1:
                is_list_item[i] = True

    chars = list(text)
    for i, is_valid in enumerate(is_list_item):
        if not is_valid:
            continue
        _, is_parens, _, _, delim, delim_start, lparen_idx, rparen_idx, lead_space_idx, _ = items[i]

        if is_parens:
            if lparen_idx >= 0 and chars[lparen_idx] == "(":
                chars[lparen_idx] = PUA_LEFT_PAREN
            if rparen_idx >= 0 and chars[rparen_idx] == ")":
                chars[rparen_idx] = PUA_RIGHT_PAREN
        elif "." in delim:
            dot_offset = delim.index(".")
            chars[delim_start + dot_offset] = PUA_PERIOD

        if lead_space_idx >= 0 and chars[lead_space_idx] == " ":
            chars[lead_space_idx] = "\r"

    return "".join(chars)


def _mask_parenthesized_and_roman_lists(text: str) -> str:
    """Mask parens and delimiters in Roman numeral list items like (i), (ii), i., ii.)."""
    chars = list(text)

    roman_parens_matches = list(ROMAN_PARENS_REGEX.finditer(text))
    if roman_parens_matches:
        r_items: list[tuple[str, int, int, int, int, int]] = []
        for m in roman_parens_matches:
            roman = m.group("roman").lower()
            lead = m.group("lead") or ""
            m_start, m_end = m.span()
            roman_start = m.start("roman")

            if roman in ROMAN_NUMERALS_SET:
                lead_space_idx = -1
                if lead and lead[0] in (" ", "\t") and m_start > 0:
                    lead_space_idx = m_start
                lparen_idx = roman_start - 1
                rparen_idx = m_end - 1
                r_items.append((roman, m_start, m_end, lparen_idx, rparen_idx, lead_space_idx))

        is_valid_r: list[bool] = [False] * len(r_items)
        for i, (roman, m_start, m_end, _, _, _) in enumerate(r_items):
            curr_idx = ROMAN_NUMERALS.index(roman)
            if i + 1 < len(r_items):
                next_roman = r_items[i + 1][0]
                next_idx = ROMAN_NUMERALS.index(next_roman)
                if next_idx == curr_idx + 1:
                    is_valid_r[i] = True
                    is_valid_r[i + 1] = True
            if i > 0:
                prev_roman = r_items[i - 1][0]
                prev_idx = ROMAN_NUMERALS.index(prev_roman)
                if prev_idx == curr_idx - 1:
                    is_valid_r[i] = True
            elif (
                m_start == 0
                or text[m_start - 1] in ("\n", "\r")
                or (m_end < len(text) and bool(re.match(r"\s+[A-Z]", text[m_end:])))
            ):
                is_valid_r[i] = True

        for i, is_valid in enumerate(is_valid_r):
            if not is_valid:
                continue
            _, _, _, lparen_idx, rparen_idx, lead_space_idx = r_items[i]
            if lparen_idx >= 0 and chars[lparen_idx] == "(":
                chars[lparen_idx] = PUA_LEFT_PAREN
            if rparen_idx >= 0 and chars[rparen_idx] == ")":
                chars[rparen_idx] = PUA_RIGHT_PAREN
            if lead_space_idx >= 0 and chars[lead_space_idx] == " ":
                chars[lead_space_idx] = "\r"

    roman_delim_matches = list(ROMAN_DELIM_REGEX.finditer(text))
    if roman_delim_matches:
        roman_items: list[tuple[str, int, int, str, int, int]] = []
        for m in roman_delim_matches:
            roman = m.group("roman").lower()
            lead = m.group("lead") or ""
            delim = m.group("delim") or ""
            m_start, m_end = m.span()
            delim_start = m.start("delim")

            if roman in ROMAN_NUMERALS_SET:
                lead_space_idx = -1
                if lead and lead[0] in (" ", "\t") and m_start > 0:
                    lead_space_idx = m_start
                roman_items.append((roman, m_start, m_end, delim, delim_start, lead_space_idx))

        is_roman_item: list[bool] = [False] * len(roman_items)
        for i, (roman, m_start, _, _, _, _) in enumerate(roman_items):
            curr_idx = ROMAN_NUMERALS.index(roman)
            if i + 1 < len(roman_items):
                next_roman = roman_items[i + 1][0]
                next_idx = ROMAN_NUMERALS.index(next_roman)
                if next_idx == curr_idx + 1:
                    is_roman_item[i] = True
                    is_roman_item[i + 1] = True
            if i > 0:
                prev_roman = roman_items[i - 1][0]
                prev_idx = ROMAN_NUMERALS.index(prev_roman)
                if prev_idx == curr_idx - 1:
                    is_roman_item[i] = True
            elif curr_idx == 0 and (m_start == 0 or text[m_start - 1] in ("\n", "\r")):
                is_roman_item[i] = True

        for i, is_valid in enumerate(is_roman_item):
            if not is_valid:
                continue
            _, _, _, delim, delim_start, lead_space_idx = roman_items[i]

            if "." in delim:
                dot_offset = delim.index(".")
                chars[delim_start + dot_offset] = PUA_PERIOD

            if lead_space_idx >= 0 and chars[lead_space_idx] == " ":
                chars[lead_space_idx] = "\r"

    return "".join(chars)


def mask_list_items(text: str, lang: str = "") -> str:
    """Mask list item periods and delimiters with PUA sentinels."""
    if not text:
        return text

    lang_module = get_language_module(lang) if lang else None
    supports_alpha: bool = getattr(lang_module, "SUPPORTS_ALPHA_LISTS", True) if lang_module else True

    text = re.sub(r"(?<=\S)\s(?=[•⁃])", "\r", text)
    text = _mask_parenthesized_and_roman_lists(text)
    text = _mask_numbered_lists(text)
    if supports_alpha:
        text = _mask_alphabetical_lists(text)
    return text


# =============================================================================
# 2. Abbreviation Disambiguation
# =============================================================================


def replace_pre_number_abbr(txt: str, abbr: str) -> str:
    """Mask periods in number-preceding abbreviations (e.g. 'No. 5', 'pp. (1-3)')."""
    escaped_abbr = re.escape(abbr.strip())
    pattern = rf"((?:(?<=^)|(?<=\s))(?i:{escaped_abbr}))\.(?=(\s*\d|\s+\())"
    return re.sub(pattern, r"\g<1>" + PUA_PERIOD, txt)


def replace_prepositive_abbr(txt: str, abbr: str) -> str:
    """Mask periods in prepositive titles and honorifics (e.g. 'Mr. Jones', 'Gen. 1:1')."""
    escaped_abbr = re.escape(abbr.strip())
    pattern = rf"((?:(?<=^)|(?<=\s))(?i:{escaped_abbr}))\.(?=(\s|:\d+))"
    return re.sub(pattern, r"\g<1>" + PUA_PERIOD, txt)


def replace_period_of_abbr(txt: str, abbr: str) -> str:
    """Mask standard abbreviation periods when followed by lowercase text, numbers, or punctuation."""
    escaped_abbr = re.escape(abbr.strip())
    pattern = (
        rf"((?:(?<=^)|(?<=\s))(?i:{escaped_abbr}))"
        r"[\u200e\u200f\u202a-\u202e\u2066-\u2069]*\."
        r"[\u200e\u200f\u202a-\u202e\u2066-\u2069]*"
        rf"(?=[.:\-?,!\"\'“”«»]|\s+(?:[a-zа-яё\u0600-\u06ff]|I\s|I'm|I'll|\d|\(|\"|'|«|„))"
    )
    return re.sub(pattern, lambda m: m.group(0).replace(".", PUA_PERIOD), txt)


def replace_multi_period_abbreviations(text: str, lang: str = "") -> str:
    """Mask all periods inside multi-period acronyms and abbreviations."""
    lang_module = get_language_module(lang) if lang else None
    mpa_pattern: re.Pattern[str] = (
        getattr(lang_module, "MULTI_PERIOD_ABBREVIATION_REGEX", MULTI_PERIOD_DEFAULT_REGEX)
        if lang_module
        else MULTI_PERIOD_DEFAULT_REGEX
    )
    return mpa_pattern.sub(lambda m: m.group(0).replace(".", PUA_PERIOD), text)


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
    return boundary_regex.sub(r"\g<1>.", text)


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
    """Disambiguate and mask abbreviations within text."""
    if not text:
        return text

    text = POSSESSIVE_ABBR_REGEX.sub(PUA_PERIOD, text)
    text = KOMMANDITGESELLSCHAFT_REGEX.sub(PUA_PERIOD, text)
    for _ in range(3):
        text = SINGLE_UPPERCASE_LETTER_REGEX.sub(r"\g<1>" + PUA_PERIOD, text)

    text = replace_multi_period_abbreviations(text, lang=lang)

    lang_module = get_language_module(lang) if lang else None
    lang_rules: tuple[Rule, ...] = getattr(lang_module, "RULES", ()) if lang_module else ()
    for rule in lang_rules:
        text = rule.pattern.sub(rule.replacement, text)

    lines: list[str] = []
    for line in text.splitlines(keepends=True):
        lines.append(search_for_abbreviations_in_string(line, lang=lang))
    text = "".join(lines)

    text = SINGLE_LOWERCASE_LETTER_REGEX.sub(r"\g<1>" + PUA_PERIOD, text)

    for rule in AM_PM_RULES:
        text = rule.pattern.sub(rule.replacement, text)

    text = replace_abbreviation_as_sentence_boundary(text, lang=lang)
    return text


# =============================================================================
# 3. Paired Punctuation Masking
# =============================================================================


def mask_between_punctuation(text: str, lang: str = "") -> str:
    """Mask punctuation enclosed within paired quotes, brackets, parens, and dashes."""
    if not text:
        return text

    if not (WORD_WITH_LEADING_APOSTROPHE.search(text) and not re.search(r"'\s", text)):
        text = BETWEEN_SINGLE_QUOTES_REGEX.sub(mask_single_quote_punctuation, text)

    for pattern, handler in STANDARD_PAIRED_PATTERNS:
        text = pattern.sub(handler, text)

    lang_module = get_language_module(lang) if lang else None
    lang_paired_patterns: tuple[re.Pattern[str], ...] = (
        getattr(lang_module, "PAIRED_PUNCTUATION_PATTERNS", ()) if lang_module else ()
    )
    for custom_pattern in lang_paired_patterns:
        text = custom_pattern.sub(mask_punctuation, text)

    return text


# =============================================================================
# 4. Processor Core Pipeline
# =============================================================================


@dataclass(slots=True)
class Processor:
    """Orchestrates sentence boundary disambiguation and segmentation."""

    text: str = ""
    lang: str = ""
    char_span: bool = False
    lang_module: ModuleType | None = field(init=False, default=None)

    def __post_init__(self) -> None:
        self.text = self.text or ""
        self.lang_module = get_language_module(self.lang) if self.lang else None

    def process(self) -> list[str]:
        """Execute the full 1:1 length-preserving disambiguation and extraction pipeline."""
        if not self.text:
            return []

        text = self.text

        # 1. Lists: Mask list numbers and format markers
        text = mask_list_items(text, lang=self.lang)

        # 2. Abbreviations: Mask periods in honorifics, initials, acronyms
        text = replace_abbreviations(text, lang=self.lang)

        # 3. Numbers & Dates: Mask decimals, versions, timestamps
        text = self._mask_numbers_and_dates(text)

        # 4. Exclamation words: Mask internal exclamation marks (e.g., 'Yahoo!')
        text = mask_exclamation_words(text)

        # 5. Paired punctuation: Mask enclosed periods/punctuation
        text = self._check_for_parens_between_quotes(text)
        text = mask_between_punctuation(text, lang=self.lang)

        # 6. Continuous & Common punctuation
        text = self._mask_continuous_punctuation(text)
        for rule in COMMON_RULES:
            text = rule.pattern.sub(rule.replacement, text)

        # 7. Boundary splitting
        return self._split_into_segments(text)

    def _check_for_parens_between_quotes(self, text: str) -> str:
        """Insert break delimiters around parenthetical citations between double quotes."""

        def _paren_replace(m: re.Match[str]) -> str:
            match = m.group(0)
            sub1 = re.sub(r"\s(?=\()", "\r", match)
            return re.sub(r"(?<=\))\s", "\r", sub1)

        return PARENS_BETWEEN_DOUBLE_QUOTES_REGEX.sub(_paren_replace, text)

    def _mask_numbers_and_dates(self, text: str) -> str:
        """Mask periods in decimal numbers, timestamps, and language-specific date formats."""
        for rule in NUMBER_RULES:
            text = rule.pattern.sub(rule.replacement, text)

        def _ref_sub(m: re.Match[str]) -> str:
            ref = m.group("ref")
            space = m.group("space") or ""
            if m.end() == len(m.string):
                return f"{PUA_PERIOD}{ref}"
            return f"{PUA_PERIOD}{ref}{space}\r"

        text = NUMBERED_REFERENCE_REGEX.sub(_ref_sub, text)

        if self.lang_module:
            for rule in getattr(self.lang_module, "RULES", ()):
                text = rule.pattern.sub(rule.replacement, text)

        return text

    def _mask_continuous_punctuation(self, text: str) -> str:
        """Mask double punctuation marks and multi-dot ellipses."""

        def _cont_repl(m: re.Match[str]) -> str:
            return m.group(1).replace("!", PUA_EXCLAMATION).replace("?", PUA_QUESTION)

        text = CONTINUOUS_PUNCTUATION_REGEX.sub(_cont_repl, text)
        for rule in DOUBLE_PUNCTUATION_RULES:
            text = rule.pattern.sub(rule.replacement, text)
        for rule in ELLIPSIS_RULES:
            text = rule.pattern.sub(rule.replacement, text)
        return text

    def _split_into_segments(self, text: str) -> list[str]:
        """Split disambiguated text into sentence segments using boundary regex."""
        boundary_regex = (
            getattr(self.lang_module, "SENTENCE_BOUNDARY_REGEX", None) if self.lang_module else None
        ) or SENTENCE_BOUNDARY_REGEX

        punctuations = (
            getattr(self.lang_module, "PUNCTUATIONS", None) if self.lang_module else None
        ) or PUNCTUATIONS

        search_punctuations = punctuations | {
            PUA_PERIOD,
            PUA_EXCLAMATION,
            PUA_QUESTION,
            PUA_DOUBLE_QE,
            PUA_DOUBLE_EQ,
            PUA_DOUBLE_QQ,
            PUA_DOUBLE_EE,
            PUA_TEMP_END_PUNCT,
        }

        quote_regex = (
            getattr(self.lang_module, "QUOTATION_AT_END_OF_SENTENCE_REGEX", None)
            if self.lang_module
            else None
        ) or QUOTATION_AT_END_OF_SENTENCE_REGEX

        split_quote_regex = (
            getattr(self.lang_module, "SPLIT_SPACE_QUOTATION_AT_END_OF_SENTENCE_REGEX", None)
            if self.lang_module
            else None
        ) or SPLIT_SPACE_QUOTATION_AT_END_OF_SENTENCE_REGEX

        segments: list[str] = []
        for line in LINE_SPLIT_REGEX.split(text):
            if not line:
                continue
            if any(p in line for p in search_punctuations):
                proc_line = line if line[-1] in punctuations else (line + PUA_TEMP_END_PUNCT)
                matches = list(boundary_regex.finditer(proc_line))
                if matches:
                    for m in matches:
                        match_str = m.group(0)
                        if quote_regex.search(match_str):
                            parts = split_quote_regex.split(match_str)
                            segments.extend(unmask_all(p).strip() for p in parts if p.strip())
                        else:
                            cleaned_seg = unmask_all(match_str).strip()
                            if cleaned_seg:
                                segments.append(cleaned_seg)
                else:
                    raw = unmask_all(line).strip()
                    if raw:
                        segments.append(raw)
            else:
                raw = unmask_all(line).strip()
                if raw:
                    segments.append(raw)

        return segments


# =============================================================================
# Legacy Compatibility Wrappers
# =============================================================================


@dataclass(slots=True)
class ListItemReplacer:
    """Legacy compatibility wrapper for list item masking."""

    ROMAN_NUMERALS: ClassVar[list[str]] = list(ROMAN_NUMERALS)
    LATIN_NUMERALS: ClassVar[list[str]] = LATIN_NUMERALS

    text: str

    def add_line_break(self) -> str:
        self.text = mask_list_items(self.text)
        return self.text

    def replace_parens(self) -> str:
        return _mask_parenthesized_and_roman_lists(self.text)

    def format_numbered_list_with_parens(self) -> None:
        self.text = _mask_numbered_lists(self.text)

    def replace_periods_in_numbered_list(self) -> None:
        self.text = _mask_numbered_lists(self.text)

    def format_numbered_list_with_periods(self) -> None:
        self.text = _mask_numbered_lists(self.text)

    def format_alphabetical_lists(self) -> str:
        self.text = _mask_alphabetical_lists(self.text)
        return self.text

    def format_roman_numeral_lists(self) -> str:
        self.text = _mask_parenthesized_and_roman_lists(self.text)
        return self.text


@dataclass(slots=True)
class AbbreviationReplacer:
    """Legacy compatibility wrapper for abbreviation disambiguation."""

    text: str
    lang: str = ""

    def replace(self) -> str:
        return replace_abbreviations(self.text, self.lang)

    def replace_abbreviation_as_sentence_boundary(self) -> None:
        self.text = replace_abbreviation_as_sentence_boundary(self.text, self.lang)

    def replace_multi_period_abbreviations(self) -> None:
        self.text = replace_multi_period_abbreviations(self.text, self.lang)

    def search_for_abbreviations_in_string(self, text: str) -> str:
        return search_for_abbreviations_in_string(text, self.lang)
