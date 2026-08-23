"""Armenian language configuration for sentence boundary disambiguation.

Armenian script uses distinctive punctuation marks:
- \u0589 (։) : Armenian Full Stop (Verjaket)
- \u055c (՜) : Armenian Exclamation Mark (Batsaganchakan Nshan)
- : (ASCII colon is also used as a boundary marker)
"""

import re

from .common.standard import Rule

ISO_CODE = "hy"

# Armenian Specific Punctuation Marks
ARMENIAN_FULL_STOP = "\u0589"  # ։
ARMENIAN_EXCLAMATION_MARK = "\u055c"  # ՜

PUNCTUATIONS: frozenset[str] = frozenset(
    {
        ARMENIAN_FULL_STOP,
        ARMENIAN_EXCLAMATION_MARK,
        ":",
    }
)

SENTENCE_STARTERS: frozenset[str] = frozenset()
ABBREVIATIONS: frozenset[str] = frozenset()
PREPOSITIVE_ABBREVIATIONS: frozenset[str] = frozenset()
NUMBER_ABBREVIATIONS: frozenset[str] = frozenset()

# Sentence boundary matching Armenian punctuation, colon, or end-of-string
SENTENCE_BOUNDARY_REGEX = re.compile(rf".*?[{ARMENIAN_FULL_STOP}{ARMENIAN_EXCLAMATION_MARK}:]|.*?$")

# Language-specific replacement rules
RULES: tuple[Rule, ...] = ()
