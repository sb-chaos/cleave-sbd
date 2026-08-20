"""Marathi (मराठी) language configuration for sentence boundary disambiguation.

Reference grammar rules: https://gopract.com/Pages/Marathi-Grammar-Viramchinah.aspx
"""

import re

from .common.standard import Rule

ISO_CODE = "mr"

PUNCTUATIONS: frozenset[str] = frozenset(
    {
        ".",
        "!",
        "?",
    }
)

SENTENCE_STARTERS: frozenset[str] = frozenset()
ABBREVIATIONS: frozenset[str] = frozenset()
PREPOSITIVE_ABBREVIATIONS: frozenset[str] = frozenset()
NUMBER_ABBREVIATIONS: frozenset[str] = frozenset()

# Sentence boundary matching standard punctuation or end-of-string
SENTENCE_BOUNDARY_REGEX = re.compile(r".*?[.!?]|.*?$")

# Language-specific replacement rules
RULES: tuple[Rule, ...] = ()
