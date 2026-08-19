"""Japanese (日本語) language configuration for sentence boundary disambiguation.

Handles Japanese-specific paired punctuation and mid-word newline cleaning:
- \uff08 / \uff09 (（ ）) : Fullwidth Parentheses
- \u300c / \u300d (「 」) : Corner Brackets (Kagikakko)
- Mid-word newline removal following the particle の (\u306e)
"""

import re

from .common.standard import Rule

ISO_CODE = "ja"

SENTENCE_STARTERS: frozenset[str] = frozenset()
ABBREVIATIONS: frozenset[str] = frozenset()
PREPOSITIVE_ABBREVIATIONS: frozenset[str] = frozenset()
NUMBER_ABBREVIATIONS: frozenset[str] = frozenset()

# Paired quotation/bracket patterns for punctuation masking
JAPANESE_PARENS_REGEX = re.compile(r"\uff08(?=(?P<tmp>[^\uff08\uff09]+|\\{2}|\\.)*)(?P=tmp)\uff09")
JAPANESE_QUOTES_REGEX = re.compile(r"\u300c(?=(?P<tmp>[^\u300c\u300d]+|\\{2}|\\.)*)(?P=tmp)\u300d")

PAIRED_PUNCTUATION_PATTERNS: tuple[re.Pattern[str], ...] = (
    JAPANESE_PARENS_REGEX,
    JAPANESE_QUOTES_REGEX,
)

# Japanese-specific preprocessing and transformation rules
RULES: tuple[Rule, ...] = (
    # Remove newlines immediately following particle の before non-whitespace
    Rule(re.compile(r"(?<=\u306e)\n(?=\S)"), ""),
)
