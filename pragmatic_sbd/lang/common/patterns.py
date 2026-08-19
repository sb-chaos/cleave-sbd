"""Pre-compiled regex patterns and transformation rules for sentence boundary disambiguation."""

from __future__ import annotations

import re
from collections.abc import Callable

from .pua import (
    PUA_DOUBLE_EE,
    PUA_DOUBLE_EQ,
    PUA_DOUBLE_QE,
    PUA_DOUBLE_QQ,
    PUA_ELLIPSIS_DOT,
    PUA_ELLIPSIS_SPACE,
    PUA_EXCLAMATION,
    PUA_NEWLINE,
    PUA_PERIOD,
    PUA_QUESTION,
    PUA_TEMP_END_PUNCT,
    Rule,
    mask_punctuation,
)

# =============================================================================
# 1. Boundary & Sentence Extraction Patterns
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
    rf"\S.*?[.\u3002\uff0e\uff01!?\uff1f{PUA_TEMP_END_PUNCT}{PUA_NEWLINE}"
    rf"{PUA_DOUBLE_QE}{PUA_DOUBLE_EQ}{PUA_DOUBLE_QQ}{PUA_DOUBLE_EE}]|"
    r"[.\u3002\uff0e\uff01!?\uff1f]"
)

QUOTATION_AT_END_OF_SENTENCE_REGEX = re.compile(
    rf"""[!?.\-{PUA_PERIOD}{PUA_EXCLAMATION}{PUA_QUESTION}]["“”]\s[A-Z]"""
)
SPLIT_SPACE_QUOTATION_AT_END_OF_SENTENCE_REGEX = re.compile(
    rf"""(?<=[!?.\-{PUA_PERIOD}{PUA_EXCLAMATION}{PUA_QUESTION}]["“”])\s(?=[A-Z])"""
)
PARENS_BETWEEN_DOUBLE_QUOTES_REGEX = re.compile(r'["”]\s\([^)]*\)\s["“]')
CONTINUOUS_PUNCTUATION_REGEX = re.compile(r"(?<=\S)([!?]{3,})(?=(\s|\Z|$))")
MULTI_PERIOD_DEFAULT_REGEX = re.compile(
    r"\b[a-zA-Z\u0400-\u0500](?:\.[a-zA-Z\u0400-\u0500])+\.", re.IGNORECASE
)

# Footnote / numbered references (e.g. "end of text.12 Next sentence", "martyr.[1]")
NUMBERED_REFERENCE_REGEX = re.compile(
    rf"(?<=[^\d\s])(?:\.|{PUA_PERIOD})"
    r"(?P<ref>(?:\[(?:\d{1,3},?\s?-?\s?)*\b\d{1,3}\])+|(?:(?:\d{1,3}\s?)?\d{1,3}))"
    r"(?P<space>\s*)(?=(?:[A-Z]|\Z|$))"
)


# =============================================================================
# 2. Pre-Compiled Transformation Rules
# =============================================================================

COMMON_RULES: tuple[Rule, ...] = (
    # Protect coordinates like 45°N. 123°W
    Rule(re.compile(r"(?<=[a-zA-Z]°)\.(?=\s*\d+)"), PUA_PERIOD),
    # Protect common file extensions
    Rule(
        re.compile(
            r"(?<=\s)\.(?=(?:jpe?g|png|gif|tiff?|pdf|ps|docx?|xlsx?|svg|bmp|"
            r"tga|exif|odt|html?|txt|rtf|bat|sxw|xml|zip|exe|msi|blend|wmv|"
            r"mp[34]|pptx?|flac|rb|cpp|cs|js)\s)"
        ),
        PUA_PERIOD,
    ),
    # Preserve isolated single newlines
    Rule(re.compile(r"\n"), PUA_NEWLINE),
    # Protect questions/exclamations inside quotes
    Rule(re.compile(r"""\?(?=['"])"""), PUA_QUESTION),
    Rule(re.compile(r"""!(?=['"])"""), PUA_EXCLAMATION),
    # Protect mid-sentence exclamation points
    Rule(re.compile(r"!(?=,\s[a-z])"), PUA_EXCLAMATION),
    Rule(re.compile(r"!(?=\s[a-z])"), PUA_EXCLAMATION),
    # Protect periods in alphanumeric words/emails (e.g. site.com)
    Rule(re.compile(r"([a-zA-Z0-9_])\.([a-zA-Z0-9_])"), r"\g<1>" + PUA_PERIOD + r"\g<2>"),
)

DOUBLE_PUNCTUATION_RULES: tuple[Rule, ...] = (
    Rule(re.compile(r"\?!"), PUA_DOUBLE_QE),
    Rule(re.compile(r"!\?"), PUA_DOUBLE_EQ),
    Rule(re.compile(r"\?\?"), PUA_DOUBLE_QQ),
    Rule(re.compile(r"!!"), PUA_DOUBLE_EE),
)

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
        re.compile(r"(?<=\S)\.{3}(?=\.\s[A-Z])"),
        PUA_ELLIPSIS_DOT * 3,
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
# 3. Paired Delimiters & Quotation Regexes
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
BETWEEN_PARENS_REGEX: re.Pattern[str] = re.compile(r"\((?=(?P<tmp_p>[^()\r\n\\]+|\\{2}|\\.)*)(?P=tmp_p)\)")
BETWEEN_SINGLE_QUOTES_REGEX: re.Pattern[str] = re.compile(
    r"(?:(?<=^)|(?<=\s))'(?!\s)(?:[^'\n\r]|(?<=[a-zA-Z])'(?=[a-zA-Z]))+?'(?=[\s.,!?;:\)\]\n\r]|$)"
)
BETWEEN_SINGLE_QUOTE_SLANTED_REGEX: re.Pattern[str] = re.compile(
    r"(?:(?<=^)|(?<=\s))\u2018(?!\s)(?:[^\u2019\n\r]|(?<=[a-zA-Z])\u2019(?=[a-zA-Z]))+?\u2019(?=[\s.,!?;:\)\]\n\r]|$)"
)
BETWEEN_EM_DASHES_REGEX: re.Pattern[str] = re.compile(r"--(?=(?P<tmp_ed>[^-\r\n]*))(?P=tmp_ed)--")
WORD_WITH_LEADING_APOSTROPHE: re.Pattern[str] = re.compile(r"(?<=\s)'(?:[^']|'[a-zA-Z])*'\S")

STANDARD_PAIRED_PATTERNS: tuple[tuple[re.Pattern[str], Callable[[re.Match[str]], str]], ...] = (
    (BETWEEN_DOUBLE_QUOTES_REGEX, mask_punctuation),
    (BETWEEN_QUOTE_ARROW_REGEX, mask_punctuation),
    (BETWEEN_QUOTE_SLANTED_REGEX, mask_punctuation),
    (BETWEEN_SQUARE_BRACKETS_REGEX, mask_punctuation),
    (BETWEEN_PARENS_REGEX, mask_punctuation),
    (BETWEEN_SINGLE_QUOTE_SLANTED_REGEX, mask_punctuation),
    (BETWEEN_EM_DASHES_REGEX, mask_punctuation),
)


# =============================================================================
# 4. List Item Regexes
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
# 5. Abbreviation Regexes
# =============================================================================

POSSESSIVE_ABBR_REGEX: re.Pattern[str] = re.compile(r"\.(?='s\b|’s\b|'S\b|’S\b)")
KOMMANDITGESELLSCHAFT_REGEX: re.Pattern[str] = re.compile(
    r"(?<=Co)\.(?=\s*(?:KG|GmbH|OHG|AG)\b)", re.IGNORECASE
)
SINGLE_UPPERCASE_LETTER_REGEX: re.Pattern[str] = re.compile(
    r"((?:(?<=^)|(?<=[\s\ue000]))[A-ZА-ЯЁ])\.(?=[,.:\-?!]|\s|[A-ZА-ЯЁ]\.|\s*$)"
)
SINGLE_LOWERCASE_LETTER_REGEX: re.Pattern[str] = re.compile(
    r"((?:(?<=^)|(?<=\s))[a-zа-яё])\.(?=\s+[a-zA-Zа-яёА-ЯЁ]|\s*$)"
)
AM_PM_REGEX: re.Pattern[str] = re.compile(r"(?<=\d)\s*(?:a\.m|p\.m|am|pm)\b", re.IGNORECASE)
