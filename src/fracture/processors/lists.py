"""Sequential list detection, validation, and PUA delimiter masking."""

from __future__ import annotations

import re

from fracture.language.protocols import LanguageProtocol
from fracture.rules import (
    ALPHA_LIST_REGEX,
    BULLET_CHARS,
    LATIN_NUMERALS,
    LEAD_WHITESPACE,
    NUMBER_LIST_REGEX,
    PUA_LEFT_PAREN,
    PUA_PERIOD,
    PUA_RIGHT_PAREN,
    ROMAN_DELIM_REGEX,
    ROMAN_NUMERALS,
    ROMAN_NUMERALS_SET,
    ROMAN_PARENS_REGEX,
)


def apply_replacements(text: str, replacements: dict[int, str]) -> str:
    """Efficiently assemble a modified string from sparse character replacements.

    Args:
        text: The original text string.
        replacements: A dictionary mapping character indices to replacement strings.

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


def mask_numbered_lists(text: str) -> str:
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
        has_bullet = any(bullet in leading_chars for bullet in BULLET_CHARS)

        leading_space_index = -1
        if leading_chars and leading_chars[0] in LEAD_WHITESPACE and match_start > 0:
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

    is_list_item = [False] * len(items)
    for index, (
        item_value,
        is_parens,
        match_start,
        _,
        _,
        _,
        _,
        _,
        _,
        has_bullet,
    ) in enumerate(items):
        if has_bullet:
            is_list_item[index] = True
            continue

        if (
            index + 1 < len(items)
            and items[index + 1][0] == item_value + 1
            and is_parens == items[index + 1][1]
            and (is_parens or items[index][4] == items[index + 1][4])
        ):
            is_list_item[index] = True
            is_list_item[index + 1] = True
        if (
            index > 0
            and items[index - 1][0] == item_value - 1
            and is_parens == items[index - 1][1]
            and (is_parens or items[index][4] == items[index - 1][4])
        ) or (
            item_value == 1
            and (match_start == 0 or text[match_start - 1] in ("\n", "\r"))
        ):
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

    return apply_replacements(text, replacements)


def mask_alphabetical_lists(text: str) -> str:
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
        has_bullet = any(bullet in leading_chars for bullet in BULLET_CHARS)

        leading_space_index = -1
        if leading_chars and leading_chars[0] in LEAD_WHITESPACE and match_start > 0:
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

    is_list_item = [False] * len(items)
    for index, (
        letter,
        is_parens,
        _match_start,
        _,
        _,
        _,
        _,
        _,
        _,
        has_bullet,
    ) in enumerate(items):
        if has_bullet:
            is_list_item[index] = True
            continue

        current_index = LATIN_NUMERALS.get(letter, -1)
        if current_index == -1:
            continue

        if (
            index + 1 < len(items)
            and LATIN_NUMERALS.get(items[index + 1][0], -1) == current_index + 1
            and is_parens == items[index + 1][1]
            and (is_parens or items[index][4] == items[index + 1][4])
        ):
            is_list_item[index] = True
            is_list_item[index + 1] = True
        if (
            index > 0
            and LATIN_NUMERALS.get(items[index - 1][0], -1) == current_index - 1
        ):
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

    return apply_replacements(text, replacements)


def mask_parenthesized_and_roman_lists(text: str) -> str:
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
                if (
                    leading_chars
                    and leading_chars[0] in LEAD_WHITESPACE
                    and match_start > 0
                ):
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
        for index, (roman, match_start, match_end, _, _, _) in enumerate(
            roman_paren_items
        ):
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
                or (
                    match_end < len(text)
                    and bool(re.match(r"\s+[A-Z]", text[match_end:]))
                )
            ):
                is_valid_roman_paren[index] = True

        for index, is_valid in enumerate(is_valid_roman_paren):
            if not is_valid:
                continue
            _, _, _, lparen_index, rparen_index, leading_space_index = (
                roman_paren_items[index]
            )
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
                if (
                    leading_chars
                    and leading_chars[0] in LEAD_WHITESPACE
                    and match_start > 0
                ):
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
            elif current_index == 0 and (
                match_start == 0 or text[match_start - 1] in ("\n", "\r")
            ):
                is_valid_roman_delim[index] = True

        for index, is_valid in enumerate(is_valid_roman_delim):
            if not is_valid:
                continue
            _, _, _, delimiter, delimiter_start, leading_space_index = (
                roman_delim_items[index]
            )

            dot_offset = delimiter.find(".")
            if dot_offset >= 0:
                replacements[delimiter_start + dot_offset] = PUA_PERIOD

            if leading_space_index >= 0 and text[leading_space_index] == " ":
                replacements[leading_space_index] = "\r"

    return apply_replacements(text, replacements)


def mask_list_items(text: str, config: LanguageProtocol | None = None) -> str:
    """Mask list item periods and delimiters with PUA sentinels.

    Args:
        text: The text string containing lists.
        config: Optional language configuration.

    Returns:
        The text with all detected list delimiters masked.
    """
    if not text:
        return text

    supports_alpha: bool = True

    if "•" in text or "⁃" in text:
        text = re.sub(r"(?<=\S)\s(?=[•⁃])", "\r", text)
    text = mask_parenthesized_and_roman_lists(text)
    text = mask_numbered_lists(text)
    if supports_alpha:
        text = mask_alphabetical_lists(text)
    return text
