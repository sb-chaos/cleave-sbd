"""Common sentence boundary patterns and numeric/abbreviation protection rules.

Replaces repetitive legacy rule classes with consolidated, pre-compiled regex tuples.
"""

import re
from typing import NamedTuple

from .standard import (
    PUA_DOUBLE_EE,
    PUA_DOUBLE_EQ,
    PUA_DOUBLE_QE,
    PUA_DOUBLE_QQ,
    PUA_NEWLINE,
    PUA_PERIOD,
    PUA_TEMP_END_PUNCT,
)


class Rule(NamedTuple):
    pattern: re.Pattern[str]
    replacement: str = ""


# =============================================================================
# Consolidated Boundary & Sentence Extraction Patterns
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

QUOTATION_AT_END_OF_SENTENCE_REGEX = re.compile(r"""[!?.\-]["'“”]\s[A-Z]""")
SPLIT_SPACE_QUOTATION_AT_END_OF_SENTENCE_REGEX = re.compile(r"""(?<=[!?.\-]["'“”])\s(?=[A-Z])""")
PARENS_BETWEEN_DOUBLE_QUOTES_REGEX = re.compile(r'["\”]\s\(.*\)\s["\“]')
CONTINUOUS_PUNCTUATION_REGEX = re.compile(r"(?<=\S)(!|\?){3,}(?=\s|$)")
MULTI_PERIOD_ABBREVIATION_REGEX = re.compile(r"\b[a-z](?:\.[a-z])+\.")

# Footnote / numbered references (e.g. "end of text.12 Next sentence")
NUMBERED_REFERENCE_REGEX = re.compile(
    rf"(?<=[^\d\s])(?:\.|{PUA_PERIOD})"
    r"(?:(?:\[(?:\d{1,3},?\s?-?\s?)*\b\d{1,3}\])+|(?:\d{1,3}\s?)?\d{1,3})"
    r"\s(?=[A-Z])"
)


# =============================================================================
# Pre-Compiled Common Transformation Rules
# =============================================================================

COMMON_ABBREVIATION_RULES: tuple[Rule, ...] = (
    # Possessive abbreviations: e.g. "U.S.'s"
    Rule(re.compile(r"\.(?='s(?:\s|$))"), PUA_PERIOD),
    # German corporate entity: "Co. KG"
    Rule(re.compile(r"(?<=Co)\.(?=\sKG)"), PUA_PERIOD),
    # Single-letter initials at line start or mid-sentence (e.g. "J. Doe", "A. Smith")
    Rule(re.compile(r"((?:(?<=^)|(?<=\s))[A-Z])\.(?=,?\s)"), rf"\1{PUA_PERIOD}"),
)

# Unmasks the terminal period in a.m. / p.m. ONLY when it ends a sentence before a capitalized word
AM_PM_RULES: tuple[Rule, ...] = (
    Rule(
        re.compile(rf"(?<=\b[AaPp]{PUA_PERIOD}[Mm]){PUA_PERIOD}(?=\s[A-Z])"),
        ".",
    ),
)

# Consolidates leading numbers, decimals, and list enumerators (1., 12., 999.)
NUMBER_RULES: tuple[Rule, ...] = (
    # Decimal starting with dot (e.g. ".5")
    Rule(re.compile(r"\.(?=\d)"), PUA_PERIOD),
    # Decimal/version within numbers (e.g. "3.14", "1.0.2")
    Rule(re.compile(r"(?<=\d)\.(?=\S)"), PUA_PERIOD),
    # Numbered list items at line start or after newline (e.g. "1. ", "12. ", "1)")
    Rule(
        re.compile(rf"((?:(?<=^)|(?<=[\r\n{PUA_NEWLINE}]))\d{{1,3}})\.(?=\s\S|\))"),
        rf"\1{PUA_PERIOD}",
    ),
)
