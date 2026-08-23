"""English language configuration for sentence boundary disambiguation.

Inherits standard abbreviations, sentence starters, and protection rules
from common.standard.
"""

from .common.standard import (
    NUMBER_ABBREVIATIONS as STD_NUMBER_ABBREVIATIONS,
    PREPOSITIVE_ABBREVIATIONS as STD_PREPOSITIVE_ABBREVIATIONS,
    SENTENCE_STARTERS as STD_SENTENCE_STARTERS,
    STANDARD_ABBREVIATIONS as STD_ABBREVIATIONS,
    Rule,
)

ISO_CODE = "en"

SENTENCE_STARTERS: frozenset[str] = STD_SENTENCE_STARTERS
ABBREVIATIONS: frozenset[str] = STD_ABBREVIATIONS
PREPOSITIVE_ABBREVIATIONS: frozenset[str] = STD_PREPOSITIVE_ABBREVIATIONS
NUMBER_ABBREVIATIONS: frozenset[str] = STD_NUMBER_ABBREVIATIONS

# English uses standard universal rules
RULES: tuple[Rule, ...] = ()
