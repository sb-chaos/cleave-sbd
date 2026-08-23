"""Urdu (اردو) language configuration for sentence boundary disambiguation.

Urdu script uses distinctive sentence-ending punctuation marks:
- \u06d4 (۔) : Urdu Full Stop (Khatma)
- \u061f (؟) : Urdu/Arabic Question Mark (Sawalama)
"""

import re

from .common.standard import Rule

ISO_CODE = "ur"

# Urdu Specific Punctuation Marks
URDU_FULL_STOP = "\u06d4"  # ۔
URDU_QUESTION_MARK = "\u061f"  # ؟

PUNCTUATIONS: frozenset[str] = frozenset(
    {
        URDU_FULL_STOP,
        URDU_QUESTION_MARK,
        "?",
        "!",
    }
)

SENTENCE_STARTERS: frozenset[str] = frozenset()
ABBREVIATIONS: frozenset[str] = frozenset()
PREPOSITIVE_ABBREVIATIONS: frozenset[str] = frozenset()
NUMBER_ABBREVIATIONS: frozenset[str] = frozenset()

# Sentence boundary matching Urdu punctuation, standard punctuation, or end-of-string
SENTENCE_BOUNDARY_REGEX = re.compile(rf".*?[{URDU_FULL_STOP}{URDU_QUESTION_MARK}!?]|.*?$")

# Language-specific replacement rules
RULES: tuple[Rule, ...] = ()
