"""List item boundary detection and disambiguation engine.

Masks periods and delimiters in numbered, alphabetical, and roman numeral lists
using Unicode Private Use Area (PUA) sentinels while preserving exact 1:1 character length.
"""

from __future__ import annotations

import re
import string
from typing import ClassVar, Final

from pragmatic_sbd.lang.common.standard import (
    PUA_LEFT_PAREN,
    PUA_PERIOD,
    PUA_RIGHT_PAREN,
    Rule,
)

# Standard Roman numerals up to 20
ROMAN_NUMERALS: Final[tuple[str, ...]] = (
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
ROMAN_NUMERALS_SET: Final[frozenset[str]] = frozenset(ROMAN_NUMERALS)
LATIN_NUMERALS: Final[list[str]] = list(string.ascii_lowercase)

# Pre-compiled declarative regular expressions

# Numbered lists: e.g. "1.", "1.)", "1)", "(1)", "• 9.", "⁃10."
NUMBER_LIST_REGEX: Final[re.Pattern[str]] = re.compile(
    r"(?P<lead>(?:^|[\r\n]|\s)(?:[•⁃\-]\s*)?)"
    r"(?:(?P<lparen>\()(?P<num_p>\d{1,3})\)|(?P<num>\d{1,3})(?P<delim>\.\)?|\)))(?=\s|$)"
)

# Alphabetical lists: e.g. "a.", "b.)", "c)", "(a)"
ALPHA_LIST_REGEX: Final[re.Pattern[str]] = re.compile(
    r"(?P<lead>(?:^|[\r\n]|\s)(?:[•⁃\-]\s*)?)"
    r"(?:(?P<lparen>\()(?P<letter_p>[a-zA-Z])\)|(?P<letter>[a-zA-Z])(?P<delim>\.\)?|\)))(?=\s|$)"
)

# Roman numeral lists in parens: e.g. "(i)", "(ii)", "(iii)"
ROMAN_PARENS_REGEX: Final[re.Pattern[str]] = re.compile(
    r"(?P<lead>(?:^|[\r\n]|\s)(?:[•⁃\-]\s*)?)\((?P<roman>[ivxldcm]+)\)(?=\s|$)",
    re.IGNORECASE,
)

# Roman numeral lists with delimiters: e.g. "i.", "ii.)", "iii)"
ROMAN_DELIM_REGEX: Final[re.Pattern[str]] = re.compile(
    r"(?P<lead>(?:^|[\r\n]|\s)(?:[•⁃\-]\s*)?)(?P<roman>[ivxldcm]+)(?P<delim>\.\)?|\))(?=\s|$)",
    re.IGNORECASE,
)


def _mask_numbered_lists(text: str) -> str:
    """Mask periods and insert breaks for numbered list items."""
    matches = list(NUMBER_LIST_REGEX.finditer(text))
    if not matches:
        return text

    items: list[tuple[int, bool, int, int, str, int, int, int, int, bool]] = []
    # (val, is_parens, m_start, m_end, delim, delim_start, lparen_idx, rparen_idx, lead_space_idx, has_bullet)
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

    # 1. Parenthesized Roman numerals (i), (ii), (iii)
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

    # 2. Roman numeral lists with delimiters: e.g. "i.", "ii.", "iii)"
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


def mask_list_items(text: str) -> str:
    """Pure functional entrypoint to mask list items and preserve 1:1 character length.

    Args:
        text (str): Input text containing potentially ambiguous list markers.

    Returns:
        str: Text with list item periods and delimiters masked with PUA sentinels
            and item breaks inserted as '\\r'.
    """
    if not text:
        return text

    # 1. Bullet item breaks (e.g. • item1 • item2)
    text = re.sub(r"(?<=\S)\s(?=[•⁃])", "\r", text)

    # 2. Parenthesized items and Roman numerals
    text = _mask_parenthesized_and_roman_lists(text)

    # 3. Numbered lists (e.g. 1., 1.), • 9., ⁃10.)
    text = _mask_numbered_lists(text)

    # 4. Alphabetical lists (e.g. a., b., c.)
    text = _mask_alphabetical_lists(text)

    return text


class ListItemReplacer:
    """Legacy compatibility wrapper for list item disambiguation and masking."""

    ROMAN_NUMERALS: ClassVar[list[str]] = list(ROMAN_NUMERALS)
    LATIN_NUMERALS: ClassVar[list[str]] = LATIN_NUMERALS

    # Legacy regex constants for backward compatibility
    ALPHABETICAL_LIST_WITH_PERIODS: ClassVar[str] = r"(?<=^)[a-z](?=\.)|(?<=\A)[a-z](?=\.)|(?<=\s)[a-z](?=\.)"
    ALPHABETICAL_LIST_WITH_PARENS: ClassVar[str] = (
        r"(?<=\()[a-z]+(?=\))|(?<=^)[a-z]+(?=\))|(?<=\A)[a-z]+(?=\))|(?<=\s)[a-z]+(?=\))"
    )
    SubstituteListPeriodRule: ClassVar[Rule] = Rule(re.compile("♨"), PUA_PERIOD)
    ListMarkerRule: ClassVar[Rule] = Rule(re.compile("☝"), "")
    SpaceBetweenListItemsFirstRule: ClassVar[Rule] = Rule(re.compile(r"(?<=\S\S)\s(?=\S\s*\d+♨)"), "\r")
    SpaceBetweenListItemsSecondRule: ClassVar[Rule] = Rule(re.compile(r"(?<=\S\S)\s(?=\d{1,2}♨)"), "\r")
    SpaceBetweenListItemsThirdRule: ClassVar[Rule] = Rule(re.compile(r"(?<=\S\S)\s(?=\d{1,2}☝)"), "\r")

    NUMBERED_LIST_REGEX_1: ClassVar[str] = (
        r"\s\d{1,2}(?=\.\s)|^\d{1,2}(?=\.\s)|\s\d{1,2}(?=\.\))|^\d{1,2}(?=\.\))|"
        r"(?<=\s\-)\d{1,2}(?=\.\s)|(?<=^\-)\d{1,2}(?=\.\s)|(?<=\s\⁃)\d{1,2}(?=\.\s)|"
        r"(?<=^\⁃)\d{1,2}(?=\.\s)|(?<=s\-)\d{1,2}(?=\.\))|(?<=^\-)\d{1,2}(?=\.\))|"
        r"(?<=\s\⁃)\d{1,2}(?=\.\))|(?<=^\⁃)\d{1,2}(?=\.\))"
    )
    NUMBERED_LIST_REGEX_2: ClassVar[str] = (
        r"(?<=\s)\d{1,2}\.(?=\s)|^\d{1,2}\.(?=\s)|(?<=\s)\d{1,2}\.(?=\))|^\d{1,2}\.(?=\))|"
        r"(?<=\s\-)\d{1,2}\.(?=\s)|(?<=^\-)\d{1,2}\.(?=\s)|(?<=\s\⁃)\d{1,2}\.(?=\s)|"
        r"(?<=^\⁃)\d{1,2}\.(?=\s)|(?<=\s\-)\d{1,2}\.(?=\))|(?<=^\-)\d{1,2}\.(?=\))|"
        r"(?<=\s\⁃)\d{1,2}\.(?=\))|(?<=^\⁃)\d{1,2}\.(?=\))"
    )
    NUMBERED_LIST_PARENS_REGEX: ClassVar[str] = r"\d{1,2}(?=\)\s)"
    EXTRACT_ALPHABETICAL_LIST_LETTERS_REGEX: ClassVar[str] = (
        r"\([a-z]+(?=\))|(?<=^)[a-z]+(?=\))|(?<=\A)[a-z]+(?=\))|(?<=\s)[a-z]+(?=\))"
    )
    ALPHABETICAL_LIST_LETTERS_AND_PERIODS_REGEX: ClassVar[str] = (
        r"(?<=^)[a-z]\.|(?<=\A)[a-z]\.|(?<=\s)[a-z]\."
    )
    ROMAN_NUMERALS_IN_PARENTHESES: ClassVar[str] = (
        r"\(((?=[mdclxvi])m*(c[md]|d?c*)(x[cl]|l?x*)(i[xv]|v?i*))\)(?=\s[A-Z])"
    )

    def __init__(self, text: str) -> None:
        self.text = text

    def add_line_break(self) -> str:
        """Run full list item disambiguation and masking pipeline."""
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
