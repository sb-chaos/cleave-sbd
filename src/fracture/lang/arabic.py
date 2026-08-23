"""Arabic language configuration for sentence boundary disambiguation.

Arabic uses distinctive punctuation marks and colon/comma behaviors:
- \u061f (؟) : Arabic Question Mark
- \u060c (،) : Arabic Comma
- Colons between digits (e.g. timestamps/ratios) are protected
- Paired listing commas are masked as non-sentence boundaries
"""

import re

from .common.standard import PUA_ARABIC_COMMA, PUA_COLON, Rule

ISO_CODE = "ar"

# Arabic Specific Punctuation Marks
ARABIC_COMMA = "\u060c"  # ،
ARABIC_QUESTION_MARK = "\u061f"  # ؟

PUNCTUATIONS: frozenset[str] = frozenset(
    {
        ".",
        "!",
        "?",
        ":",
        ARABIC_QUESTION_MARK,
        ARABIC_COMMA,
    }
)

SENTENCE_STARTERS: frozenset[str] = frozenset()
PREPOSITIVE_ABBREVIATIONS: frozenset[str] = frozenset()
NUMBER_ABBREVIATIONS: frozenset[str] = frozenset()

# Deduplicated Arabic Abbreviations
ABBREVIATIONS: frozenset[str] = frozenset(
    {
        "ا",
        "ا. د",
        "ا.د",
        "ا.ش.ا",
        "إلخ",
        "ت.ب",
        "ج.ب",
        "جم",
        "ج.م.ع",
        "س.ت",
        "سم",
        "ص.ب.",
        "ص.ب",
        "كج.",
        "كلم.",
        "م",
        "م.ب",
        "ه",
    }
)

# Sentence boundary matching terminating punctuation, colon, comma, or end-of-string
SENTENCE_BOUNDARY_REGEX = re.compile(rf".*?[:.!?{ARABIC_QUESTION_MARK}{ARABIC_COMMA}]|.*?$")

# Language-specific protection rules
RULES: tuple[Rule, ...] = (
    # Protect colons between digits (e.g., timestamps "12:30" or ratios "1:2")
    Rule(re.compile(r"(?<=\d):(?=\d)"), PUA_COLON),
    # Protect non-sentence boundary commas between phrases (e.g. "، ... ،")
    Rule(re.compile(rf"{ARABIC_COMMA}(?=\s\S+{ARABIC_COMMA})"), PUA_ARABIC_COMMA),
)
