"""Boundary extraction patterns, quotation rules, and paired delimiter regexes."""

from __future__ import annotations

import re
from collections.abc import Callable

from fracture.rules.disambiguation import Rule
from fracture.rules.pua import (
    PUA_ELLIPSIS_DOT,
    PUA_ELLIPSIS_SPACE,
    PUA_EXCLAMATION,
    PUA_NEWLINE,
    PUA_PERIOD,
    PUA_QUESTION,
    PUA_TEMP_END_PUNCT,
    mask_punctuation,
)

# =============================================================================
# Boundary & Sentence Extraction Patterns
# =============================================================================

# Matches sentences enclosed in quotes/parens, multi-punctuation runs, or terminating marks
SENTENCE_BOUNDARY_REGEX = re.compile(
    r"（(?:[^）])*）(?=\s?[A-Z])|"
    r"「(?:[^」])*」(?=\s[A-Z])|"
    r"\((?:[^\)]){2,}\)(?=\s[A-Z])|"
    r"\'(?:[^\'])*[^,]\'(?=\s[A-Z])|"
    r"\"(?:[^\"])*[^,]\"(?=\s[A-Z])|"
    r"\“(?:[^\”])*[^,]\”(?=\s[A-Z])|"
    r"[\u3002\uff0e.\uff01!?\uff1f ]{2,}|"
    rf"\S.*?[.\u3002\uff0e\uff01!?\uff1f{PUA_TEMP_END_PUNCT}{PUA_NEWLINE}]+|"
    r"[.\u3002\uff0e\uff01!?\uff1f]"
)

QUOTATION_AT_END_OF_SENTENCE_REGEX = re.compile(
    rf"""[!?.\-{PUA_PERIOD}{PUA_EXCLAMATION}{PUA_QUESTION}]["“”]\s[A-Z]"""
)
SPLIT_SPACE_QUOTATION_AT_END_OF_SENTENCE_REGEX = re.compile(
    rf"""(?<=[!?.\-{PUA_PERIOD}{PUA_EXCLAMATION}{PUA_QUESTION}]["“”])\s(?=[A-Z])"""
)
PARENS_BETWEEN_DOUBLE_QUOTES_REGEX = re.compile(r'["”]\s\([^)]*\)\s["“]')

LINE_SPLIT_REGEX: re.Pattern[str] = re.compile(rf"(?:\r\n|\r|\n|{PUA_NEWLINE})")
BULLET_CHARS: frozenset[str] = frozenset({"•", "⁃"})
LEAD_WHITESPACE: frozenset[str] = frozenset({" ", "\t"})
BULLET_SPACING_REGEX: re.Pattern[str] = re.compile(r"(?<=\S)\s(?=[•⁃])")
SINGLE_QUOTE_SPACING_REGEX: re.Pattern[str] = re.compile(r"'\s")
PARENS_LEAD_SPACE_REGEX: re.Pattern[str] = re.compile(r"\s(?=\()")
PARENS_TRAIL_SPACE_REGEX: re.Pattern[str] = re.compile(r"(?<=\))\s")

# Footnote / numbered references (e.g. "end of text.12 Next sentence", "martyr.[1]")
NUMBERED_REFERENCE_REGEX: re.Pattern[str] = re.compile(
    rf"(?<=[^\d\s])(?:\.|{PUA_PERIOD})"
    r"(?P<ref>(?:\[(?:\d{1,3},?\s?-?\s?)*\b\d{1,3}\])+|(?:(?:\d{1,3}\s?)?\d{1,3}))"
    r"(?P<space>\s*)(?=(?:[A-Z]|\Z|$))"
)


# =============================================================================
# Pre-Compiled Transformation Rules
# =============================================================================

# Common file extensions for URL / attachment protection
FILE_EXTENSIONS: str = (
    r"jpe?g|png|gif|tiff?|pdf|ps|docx?|xlsx?|svg|bmp|"
    r"tga|exif|odt|html?|txt|rtf|bat|sxw|xml|zip|exe|msi|blend|wmv|"
    r"mp[34]|pptx?|flac|rb|cpp|cs|js"
)

COMMON_RULES: tuple[Rule, ...] = (
    Rule(re.compile(r"(?<=[a-zA-Z]°)\.(?=\s*\d+)"), PUA_PERIOD),
    Rule(
        re.compile(rf"(?<=\s)\.(?=(?:{FILE_EXTENSIONS})\s)"),
        PUA_PERIOD,
    ),
    Rule(re.compile(r"""\?(?=['"])"""), PUA_QUESTION),
    Rule(re.compile(r"""!(?=['"])"""), PUA_EXCLAMATION),
    Rule(re.compile(r"!(?=,\s[a-z])"), PUA_EXCLAMATION),
    Rule(re.compile(r"!(?=\s[a-z])"), PUA_EXCLAMATION),
    Rule(re.compile(r"(?<=[a-zA-Z0-9_])\.(?=[a-zA-Z0-9_])"), PUA_PERIOD),
)


def mask_common_rules(text: str) -> str:
    """Apply all common punctuation rules across fast compiled C-level regex passes.

    Args:
        text: The input text to transform.

    Returns:
        The text with coordinates, file extensions, and punctuation masked.
    """
    has_period = "." in text
    has_quest = "?" in text
    has_excl = "!" in text

    if has_period and "°" in text:
        text = COMMON_RULES[0].pattern.sub(COMMON_RULES[0].replacement, text)
    if has_period:
        text = COMMON_RULES[1].pattern.sub(COMMON_RULES[1].replacement, text)
    if has_quest:
        text = COMMON_RULES[2].pattern.sub(COMMON_RULES[2].replacement, text)
    if has_excl:
        text = COMMON_RULES[3].pattern.sub(COMMON_RULES[3].replacement, text)
        text = COMMON_RULES[4].pattern.sub(COMMON_RULES[4].replacement, text)
        text = COMMON_RULES[5].pattern.sub(COMMON_RULES[5].replacement, text)
    if has_period:
        text = COMMON_RULES[6].pattern.sub(COMMON_RULES[6].replacement, text)

    return text


ELLIPSIS_RULES: tuple[Rule, ...] = (
    Rule(
        re.compile(r"(\s\.){3}\s"),
        (PUA_ELLIPSIS_SPACE + PUA_ELLIPSIS_DOT) * 3 + PUA_ELLIPSIS_SPACE,
    ),
    Rule(
        re.compile(r"(?<=[a-z])(\.\s){3}\.(?=$|\n)"),
        (PUA_ELLIPSIS_DOT + PUA_ELLIPSIS_SPACE) * 3 + PUA_ELLIPSIS_DOT,
    ),
    Rule(
        re.compile(r"(?<=\S)\.{4}(?=\s+[A-Z])"),
        PUA_ELLIPSIS_DOT * 3 + ".",
    ),
    Rule(
        re.compile(r"\.\.\.(?=\s+[A-Z])"),
        PUA_ELLIPSIS_DOT * 2 + ".",
    ),
    Rule(
        re.compile(r"\.\.\."),
        PUA_ELLIPSIS_DOT * 3,
    ),
)


# =============================================================================
# Paired Delimiters & Quotation Regexes
# =============================================================================

BETWEEN_DOUBLE_QUOTES_REGEX: re.Pattern[str] = re.compile(
    r'"(?=(?P<tmp_dq>[^"\r\n\\]+|\\{2}|\\.)*)(?P=tmp_dq)"'
)
BETWEEN_QUOTE_ARROW_REGEX: re.Pattern[str] = re.compile(
    r"\u00ab(?=(?P<tmp_arr>[^\u00bb\r\n\\]+|\\{2}|\\.)*)(?P=tmp_arr)\u00bb"
)
BETWEEN_QUOTE_SLANTED_REGEX: re.Pattern[str] = re.compile(
    r"\u201c(?=(?P<tmp_sq>[^\u201d\r\n\\]+|\\{2}|\\.)*)(?P=tmp_sq)\u201d"
)
BETWEEN_SQUARE_BRACKETS_REGEX: re.Pattern[str] = re.compile(
    r"\[(?=(?P<tmp_sb>[^\]\r\n\\]+|\\{2}|\\.)*)(?P=tmp_sb)\]"
)
BETWEEN_PARENS_REGEX: re.Pattern[str] = re.compile(
    r"\((?=(?P<tmp_p>[^()\r\n\\]+|\\{2}|\\.)*)(?P=tmp_p)\)"
)
BETWEEN_SINGLE_QUOTES_REGEX: re.Pattern[str] = re.compile(
    r"(?:(?<=^)|(?<=\s))'(?!\s)"
    r"[^'\n\r]+"
    r"(?:(?<=[a-zA-Z])'(?=[a-zA-Z])[^'\n\r]+)*"
    r"'(?=[\s.,!?;:\)\]\n\r]|$)"
)
BETWEEN_SINGLE_QUOTE_SLANTED_REGEX: re.Pattern[str] = re.compile(
    r"(?:(?<=^)|(?<=\s))\u2018(?!\s)"
    r"[^\u2019\n\r]+"
    r"(?:(?<=[a-zA-Z])\u2019(?=[a-zA-Z])[^\u2019\n\r]+)*"
    r"\u2019(?=[\s.,!?;:\)\]\n\r]|$)"
)
BETWEEN_EM_DASHES_REGEX: re.Pattern[str] = re.compile(
    r"--(?=(?P<tmp_ed>[^-\r\n]*))(?P=tmp_ed)--"
)
WORD_WITH_LEADING_APOSTROPHE: re.Pattern[str] = re.compile(
    r"(?<=\s)'(?:[^']|'[a-zA-Z])*'\S"
)

STANDARD_PAIRED_PATTERNS: tuple[
    tuple[re.Pattern[str], Callable[[re.Match[str]], str]], ...
] = (
    (BETWEEN_DOUBLE_QUOTES_REGEX, mask_punctuation),
    (BETWEEN_QUOTE_ARROW_REGEX, mask_punctuation),
    (BETWEEN_QUOTE_SLANTED_REGEX, mask_punctuation),
    (BETWEEN_SQUARE_BRACKETS_REGEX, mask_punctuation),
    (BETWEEN_PARENS_REGEX, mask_punctuation),
    (BETWEEN_SINGLE_QUOTE_SLANTED_REGEX, mask_punctuation),
    (BETWEEN_EM_DASHES_REGEX, mask_punctuation),
)
