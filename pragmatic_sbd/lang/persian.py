"""Persian (فارسی) language configuration for sentence boundary disambiguation.

Persian uses Arabic-script punctuation marks and specific colon/comma rules:
- \u061f (؟) : Persian/Arabic Question Mark
- \u060c (،) : Persian/Arabic Comma (masked between paired phrases)
- Colons between digits (e.g. timestamps/ratios) are protected
"""

import re

from .common.standard import PUA_ARABIC_COMMA, PUA_COLON, Rule

ISO_CODE = "fa"

# Persian/Arabic Specific Punctuation Marks
PERSIAN_QUESTION_MARK = "\u061f"  # ؟
PERSIAN_COMMA = "\u060c"  # ،

PUNCTUATIONS: frozenset[str] = frozenset(
    {
        ".",
        "!",
        "?",
        ":",
        PERSIAN_QUESTION_MARK,
    }
)

SENTENCE_STARTERS: frozenset[str] = frozenset()
ABBREVIATIONS: frozenset[str] = frozenset()
PREPOSITIVE_ABBREVIATIONS: frozenset[str] = frozenset()
NUMBER_ABBREVIATIONS: frozenset[str] = frozenset()

# Sentence boundary matching terminating punctuation, colon, or end-of-string
SENTENCE_BOUNDARY_REGEX = re.compile(rf".*?[:.!?{PERSIAN_QUESTION_MARK}]|.*?$")

# Language-specific protection rules
RULES: tuple[Rule, ...] = (
    # Protect colons between digits (e.g., timestamps "12:30" or ratios "1:2")
    Rule(re.compile(r"(?<=\d):(?=\d)"), PUA_COLON),
    # Protect non-sentence boundary commas between phrases (e.g. "، ... ،")
    Rule(re.compile(rf"{PERSIAN_COMMA}(?=\s\S+{PERSIAN_COMMA})"), PUA_ARABIC_COMMA),
)
