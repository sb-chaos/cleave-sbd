"""Chinese language configuration for sentence boundary disambiguation.

Handles Chinese-specific paired bracket and quotation masking:
- \u300a / \u300b (《 》) : Double Angle Quotation Marks / Book Title Marks
- \u300c / \u300d (「 」) : Corner Brackets / Quotation Marks
"""

import re

from .common.standard import Rule

ISO_CODE = "zh"

SENTENCE_STARTERS: frozenset[str] = frozenset()
ABBREVIATIONS: frozenset[str] = frozenset()
PREPOSITIVE_ABBREVIATIONS: frozenset[str] = frozenset()
NUMBER_ABBREVIATIONS: frozenset[str] = frozenset()

# Paired quotation/bracket patterns for punctuation masking
DOUBLE_ANGLE_QUOTES_REGEX = re.compile(r"\u300a(?=(?P<tmp>[^\u300b\\]+|\\{2}|\\.)*)(?P=tmp)\u300b")
CORNER_BRACKETS_REGEX = re.compile(r"\u300c(?=(?P<tmp>[^\u300d\\]+|\\{2}|\\.)*)(?P=tmp)\u300d")

PAIRED_PUNCTUATION_PATTERNS: tuple[re.Pattern[str], ...] = (
    DOUBLE_ANGLE_QUOTES_REGEX,
    CORNER_BRACKETS_REGEX,
)

# Standard language rules (none beyond paired bracket masking)
RULES: tuple[Rule, ...] = ()
