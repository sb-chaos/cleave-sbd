"""Hindi (हिन्दी) language configuration for sentence boundary disambiguation.

Devanagari script uses distinctive sentence-ending punctuation:
- \u0964 (।) : Devanagari Danda (Sentence Boundary)
- | : Standard vertical pipe (often used interchangeably with Danda in digital text)
"""

import re

from .common.standard import Rule

ISO_CODE = "hi"

# Devanagari Danda Marker
DEVANAGARI_DANDA = "\u0964"  # ।

PUNCTUATIONS: frozenset[str] = frozenset(
    {
        DEVANAGARI_DANDA,
        "|",
        ".",
        "!",
        "?",
    }
)

SENTENCE_STARTERS: frozenset[str] = frozenset()
ABBREVIATIONS: frozenset[str] = frozenset()
PREPOSITIVE_ABBREVIATIONS: frozenset[str] = frozenset()
NUMBER_ABBREVIATIONS: frozenset[str] = frozenset()

# Sentence boundary matching Danda, pipe, standard punctuation, or end-of-string
SENTENCE_BOUNDARY_REGEX = re.compile(rf".*?[{DEVANAGARI_DANDA}\|.!?]|.*?$")

# Language-specific replacement rules
RULES: tuple[Rule, ...] = ()
