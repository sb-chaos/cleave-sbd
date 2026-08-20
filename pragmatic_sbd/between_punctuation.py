"""Punctuation masking inside paired delimiters and quotations.

Masks sentence-terminating punctuation marks (., !, ?, etc.) enclosed within
quotes, brackets, parentheses, and dashes to prevent false-positive sentence
splits within dialogue, citations, and parenthetical clauses.
"""

import re
from collections.abc import Callable

from .lang.common.standard import (
    PUA_CJK_PERIOD,
    PUA_EXCLAMATION,
    PUA_FULLWIDTH_EXCL,
    PUA_FULLWIDTH_PERIOD,
    PUA_FULLWIDTH_QUEST,
    PUA_PERIOD,
    PUA_QUESTION,
)

# Standard punctuation masking mapping inside paired delimiters
PUNCTUATION_MASK_TABLE = str.maketrans(
    {
        ".": PUA_PERIOD,
        "!": PUA_EXCLAMATION,
        "?": PUA_QUESTION,
        "\u3002": PUA_CJK_PERIOD,  # CJK Period (。)
        "\uff01": PUA_FULLWIDTH_EXCL,  # Fullwidth Exclamation (！)
        "\uff1f": PUA_FULLWIDTH_QUEST,  # Fullwidth Question (？)
        "\uff0e": PUA_FULLWIDTH_PERIOD,  # Fullwidth Period (．)
    }
)


def mask_punctuation(match: re.Match[str]) -> str:
    """Mask sentence-ending punctuation inside matched quoted or bracketed substring."""
    return match.group(0).translate(PUNCTUATION_MASK_TABLE)


def mask_single_quote_punctuation(match: re.Match[str]) -> str:
    """Mask punctuation inside single quotes while preserving standard contractions."""
    return match.group(0).translate(PUNCTUATION_MASK_TABLE)


# fmt: off
# Pre-compiled atomic-lookahead regexes for paired delimiters
BETWEEN_DOUBLE_QUOTES_REGEX = re.compile(
    r'"(?=(?P<tmp_dq>[^"\\]+|\\{2}|\\.)*)(?P=tmp_dq)"'
)
BETWEEN_QUOTE_ARROW_REGEX = re.compile(
    r"\u00ab(?=(?P<tmp_arr>[^\u00bb\\]+|\\{2}|\\.)*)(?P=tmp_arr)\u00bb"
)
BETWEEN_QUOTE_SLANTED_REGEX = re.compile(
    r"\u201c(?=(?P<tmp_sq>[^\u201d\\]+|\\{2}|\\.)*)(?P=tmp_sq)\u201d"
)
BETWEEN_SQUARE_BRACKETS_REGEX = re.compile(
    r"\[(?=(?P<tmp_sb>[^\]\\]+|\\{2}|\\.)*)(?P=tmp_sb)\]"
)
BETWEEN_PARENS_REGEX = re.compile(
    r"\((?=(?P<tmp_p>[^()\\]+|\\{2}|\\.)*)(?P=tmp_p)\)"
)
BETWEEN_SINGLE_QUOTES_REGEX = re.compile(
    r"(?:(?<=^)|(?<=\s))'(?:[^']|'[a-zA-Z])*'"
)
BETWEEN_SINGLE_QUOTE_SLANTED_REGEX = re.compile(
    r"(?:(?<=^)|(?<=\s))\u2018(?:[^\u2019]|\u2019[a-zA-Z])*\u2019"
)
BETWEEN_EM_DASHES_REGEX = re.compile(
    r"--(?=(?P<tmp_ed>[^-]*))(?P=tmp_ed)--"
)
WORD_WITH_LEADING_APOSTROPHE = re.compile(
    r"(?<=\s)'(?:[^']|'[a-zA-Z])*'\S"
)
# fmt: on

STANDARD_PAIRED_PATTERNS: tuple[tuple[re.Pattern[str], Callable[[re.Match[str]], str]], ...] = (
    (BETWEEN_DOUBLE_QUOTES_REGEX, mask_punctuation),
    (BETWEEN_QUOTE_ARROW_REGEX, mask_punctuation),
    (BETWEEN_QUOTE_SLANTED_REGEX, mask_punctuation),
    (BETWEEN_SQUARE_BRACKETS_REGEX, mask_punctuation),
    (BETWEEN_PARENS_REGEX, mask_punctuation),
    (BETWEEN_SINGLE_QUOTE_SLANTED_REGEX, mask_punctuation),
    (BETWEEN_EM_DASHES_REGEX, mask_punctuation),
)


def mask_between_punctuation(text: str, lang: str = "") -> str:
    """Pure functional interface to mask punctuation within paired delimiters."""
    if not text:
        return text

    # 1. Single quotes with apostrophe collision check
    if not (WORD_WITH_LEADING_APOSTROPHE.search(text) and not re.search(r"'\s", text)):
        text = BETWEEN_SINGLE_QUOTES_REGEX.sub(mask_single_quote_punctuation, text)

    # 2. Standard paired patterns (double quotes, brackets, parens, em-dashes, etc.)
    for pattern, handler in STANDARD_PAIRED_PATTERNS:
        text = pattern.sub(handler, text)

    # 3. Language-specific paired patterns (e.g., Japanese 「」/（）, Slovak „“, German „“/,,“)
    from pragmatic_sbd.languages import get_language_module

    lang_module = get_language_module(lang) if lang else None
    lang_paired_patterns: tuple[re.Pattern[str], ...] = (
        getattr(lang_module, "PAIRED_PUNCTUATION_PATTERNS", ()) if lang_module else ()
    )

    for custom_pattern in lang_paired_patterns:
        text = custom_pattern.sub(mask_punctuation, text)

    return text


class BetweenPunctuation:
    """Masks punctuation occurring between paired quotes, brackets, and delimiters."""

    def __init__(self, text: str, lang: str = "") -> None:
        self.text = text
        self.lang = lang

    def replace(self) -> str:
        """Run full punctuation masking pipeline for paired delimiters."""
        return mask_between_punctuation(self.text, self.lang)

    def sub_punctuation_between_quotes_and_parens(self, txt: str) -> str:
        """Apply all standard and language-specific paired punctuation substitutions."""
        return mask_between_punctuation(txt, self.lang)

    def sub_punctuation_between_single_quotes(self, txt: str) -> str:
        """Mask punctuation inside single quotes, avoiding isolated apostrophes."""
        if WORD_WITH_LEADING_APOSTROPHE.search(txt) and not re.search(r"'\s", txt):
            return txt
        return BETWEEN_SINGLE_QUOTES_REGEX.sub(mask_single_quote_punctuation, txt)

    # Convenience helper methods preserved for backward compatibility
    def sub_punctuation_between_parens(self, txt: str) -> str:
        return BETWEEN_PARENS_REGEX.sub(mask_punctuation, txt)

    def sub_punctuation_between_square_brackets(self, txt: str) -> str:
        return BETWEEN_SQUARE_BRACKETS_REGEX.sub(mask_punctuation, txt)

    def sub_punctuation_between_double_quotes(self, txt: str) -> str:
        return BETWEEN_DOUBLE_QUOTES_REGEX.sub(mask_punctuation, txt)

    def sub_punctuation_between_quotes_arrow(self, txt: str) -> str:
        return BETWEEN_QUOTE_ARROW_REGEX.sub(mask_punctuation, txt)

    def sub_punctuation_between_em_dashes(self, txt: str) -> str:
        return BETWEEN_EM_DASHES_REGEX.sub(mask_punctuation, txt)

    def sub_punctuation_between_quotes_slanted(self, txt: str) -> str:
        return BETWEEN_QUOTE_SLANTED_REGEX.sub(mask_punctuation, txt)

    def sub_punctuation_between_single_quote_slanted(self, txt: str) -> str:
        return BETWEEN_SINGLE_QUOTE_SLANTED_REGEX.sub(mask_punctuation, txt)
