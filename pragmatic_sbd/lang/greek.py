"""Greek (Ελληνικά) language configuration for sentence boundary disambiguation.

In Greek, the semicolon (;) serves as the question mark:
- ; : Greek Question Mark (Erotimatiko)
- . : Full Stop (Teleia)
- ! : Exclamation Mark (Thavmastiko)
"""

import re

from .common.standard import Rule

ISO_CODE = "el"

# Greek uses the semicolon (;) as a question mark
PUNCTUATIONS: frozenset[str] = frozenset(
    {
        ".",
        ";",
        "!",
        "?",
    }
)

SENTENCE_STARTERS: frozenset[str] = frozenset()
ABBREVIATIONS: frozenset[str] = frozenset()
PREPOSITIVE_ABBREVIATIONS: frozenset[str] = frozenset()
NUMBER_ABBREVIATIONS: frozenset[str] = frozenset()

# Sentence boundary matching terminating punctuation (including Greek semicolon) or end-of-string
SENTENCE_BOUNDARY_REGEX = re.compile(r".*?[.;!?]|.*?$")

# Language-specific replacement rules
RULES: tuple[Rule, ...] = ()
