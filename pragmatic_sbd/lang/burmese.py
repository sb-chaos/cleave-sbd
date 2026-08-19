"""Burmese language configuration for sentence boundary disambiguation.

Myanmar script uses distinctive punctuation marks:
- \u104b (။) : Myanmar Sign Section (Double Danfa / Sentence Boundary)
- \u104f (၏) : Myanmar Symbol Genitive / Sentence Ending Marker
"""

import re

from .common.standard import Rule

ISO_CODE = "my"

# Myanmar Specific Punctuation Marks
MYANMAR_SECTION = "\u104b"  # ။
MYANMAR_GENITIVE_END = "\u104f"  # ၏

PUNCTUATIONS: frozenset[str] = frozenset(
    {
        MYANMAR_SECTION,
        MYANMAR_GENITIVE_END,
        "?",
        "!",
    }
)

SENTENCE_STARTERS: frozenset[str] = frozenset()
ABBREVIATIONS: frozenset[str] = frozenset()
PREPOSITIVE_ABBREVIATIONS: frozenset[str] = frozenset()
NUMBER_ABBREVIATIONS: frozenset[str] = frozenset()

# Sentence boundary matching Myanmar punctuation or end-of-string
SENTENCE_BOUNDARY_REGEX = re.compile(rf".*?[{MYANMAR_SECTION}{MYANMAR_GENITIVE_END}!?]|.*?$")

# Language-specific replacement rules
RULES: tuple[Rule, ...] = ()
