"""Amharic language configuration for sentence boundary disambiguation.

Ethiopic script uses distinctive punctuation marks:
- \u1362 (።) : Arat Neteb (Ethiopic Full Stop)
- \u1365 (፧) : Neteb Serey (Ethiopic Question Mark)
"""

import re

from .common.standard import Rule

ISO_CODE = "am"

# Ethiopic Punctuation Marks
ETHIOPIC_FULL_STOP = "\u1362"  # ።
ETHIOPIC_QUESTION_MARK = "\u1365"  # ፧

PUNCTUATIONS: frozenset[str] = frozenset(
    {
        ETHIOPIC_FULL_STOP,
        ETHIOPIC_QUESTION_MARK,
        "?",
        "!",
    }
)

# Amharic does not use capitalized sentence starters
SENTENCE_STARTERS: frozenset[str] = frozenset()

# No default Latin abbreviations
ABBREVIATIONS: frozenset[str] = frozenset()
PREPOSITIVE_ABBREVIATIONS: frozenset[str] = frozenset()
NUMBER_ABBREVIATIONS: frozenset[str] = frozenset()

# Sentence boundary regex matching Ethiopic punctuation or end-of-string
SENTENCE_BOUNDARY_REGEX = re.compile(rf".*?[{ETHIOPIC_QUESTION_MARK}{ETHIOPIC_FULL_STOP}!?]|.*?$")

# Language-specific replacement rules (none required beyond standard masking)
RULES: tuple[Rule, ...] = ()
