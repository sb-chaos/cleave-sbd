"""Rule definitions, exclamation lexicons, and disambiguation helpers."""

from __future__ import annotations

import re
from typing import NamedTuple

from csbd.rules.pua import PUA_EXCLAMATION


class Rule(NamedTuple):
    """Immutable rule specification containing a compiled regex and replacement template."""

    pattern: re.Pattern[str]
    replacement: str = ""


# =============================================================================
# Standard Punctuation & Sentence Starters
# =============================================================================

PUNCTUATIONS: frozenset[str] = frozenset(
    {".", "!", "?", "\u3002", "\uff0e", "\uff01", "\uff1f"}
)

# fmt: off
SENTENCE_STARTERS: frozenset[str] = frozenset({
    "A", "Being", "Did", "For", "He", "How", "However", "I", "In", "It",
    "Millions", "More", "She", "That", "The", "There", "They", "We", "What",
    "When", "Where", "Who", "Why",
})
# fmt: on


# =============================================================================
# Exclamation Words & Click Consonant Masking
# =============================================================================

EXCLAMATION_WORDS: tuple[str, ...] = (
    "ǃʼOǃKung",
    "!Kung-Ekoka",
    "!Xuun",
    "ǃKhung",
    "ǃXung",
    "!Kung",
    "!Xun",
    "!Xũ",
    "ǃXû",
    "ǃXo",
    "ǃKu",
    "ǃHu",
    "ǃung",
    "Yahoo!",
    "Yum!",
    "Y!J",
)

EXCLAMATION_RULES: tuple[Rule, ...] = tuple(
    Rule(
        pattern=re.compile(re.escape(word)),
        replacement=word.replace("!", PUA_EXCLAMATION),
    )
    for word in sorted(EXCLAMATION_WORDS, key=len, reverse=True)
)


def mask_exclamation_words(text: str) -> str:
    """Mask exclamation marks within known proper nouns and click consonants."""
    for rule in EXCLAMATION_RULES:
        text = rule.pattern.sub(rule.replacement, text)
    return text
