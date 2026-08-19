"""Unicode Private Use Area (PUA) sentinels, rule models, and unmasking engine.

Replaces arbitrary multi-character / esoteric unicode symbols with dedicated
Unicode Private Use Area (PUA) codepoints (\ue000 - \ue024) to guarantee:
1. 1:1 character length invariance (spans and offsets stay exact).
2. O(1) set-based abbreviation lookups.
3. C-speed string unmasking via str.translate with zero regex overhead.
"""

from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Rule:
    """Immutable rule specification containing a compiled regex and replacement template."""

    pattern: re.Pattern[str]
    replacement: str = ""


# =============================================================================
# Unicode Private Use Area (PUA) Sentinel Assignments
# =============================================================================

# Standard Sentence Punctuation (\ue000 - \ue007)
PUA_PERIOD = "\ue000"  # .
PUA_CJK_PERIOD = "\ue001"  # \u3002 (。)
PUA_FULLWIDTH_PERIOD = "\ue002"  # \uff0e (．)
PUA_FULLWIDTH_EXCL = "\ue003"  # \uff01 (！)
PUA_EXCLAMATION = "\ue004"  # !
PUA_QUESTION = "\ue005"  # ?
PUA_FULLWIDTH_QUEST = "\ue006"  # \uff1f (？)
PUA_APOSTROPHE = "\ue007"  # '

# Structural Delimiters & Parentheses (\ue008 - \ue00f)
PUA_LEFT_PAREN = "\ue008"  # (
PUA_RIGHT_PAREN = "\ue009"  # )
PUA_NEWLINE = "\ue00a"  # \n
PUA_TEMP_END_PUNCT = "\ue00b"  # Temporary boundary marker
PUA_ARABIC_COMMA = "\ue00c"  # \u060c (،)
PUA_COLON = "\ue00d"  # :

# Double / Mixed Punctuation (\ue010 - \ue013)
PUA_DOUBLE_QE = "\ue010"  # ?!
PUA_DOUBLE_EQ = "\ue011"  # !?
PUA_DOUBLE_QQ = "\ue012"  # ??
PUA_DOUBLE_EE = "\ue013"  # !!

# Ellipsis Sentinels (1:1 length preservation) (\ue020 - \ue021)
PUA_ELLIPSIS_DOT = "\ue020"  # Protected dot inside an ellipsis
PUA_ELLIPSIS_SPACE = "\ue021"  # Protected space inside a spaced ellipsis


# =============================================================================
# Global Fast Unmask Translation Table
# =============================================================================

UNMASK_TABLE = str.maketrans(
    {
        PUA_PERIOD: ".",
        PUA_CJK_PERIOD: "\u3002",
        PUA_FULLWIDTH_PERIOD: "\uff0e",
        PUA_FULLWIDTH_EXCL: "\uff01",
        PUA_EXCLAMATION: "!",
        PUA_QUESTION: "?",
        PUA_FULLWIDTH_QUEST: "\uff1f",
        PUA_APOSTROPHE: "'",
        PUA_LEFT_PAREN: "(",
        PUA_RIGHT_PAREN: ")",
        PUA_NEWLINE: "\n",
        PUA_TEMP_END_PUNCT: "",
        PUA_ARABIC_COMMA: "\u060c",
        PUA_COLON: ":",
        PUA_DOUBLE_QE: "?!",
        PUA_DOUBLE_EQ: "!?",
        PUA_DOUBLE_QQ: "??",
        PUA_DOUBLE_EE: "!!",
        PUA_ELLIPSIS_DOT: ".",
        PUA_ELLIPSIS_SPACE: " ",
    }
)


def unmask_all(text: str) -> str:
    """Restore all PUA sentinels back to original text in a single C-level pass."""
    return text.translate(UNMASK_TABLE)


# =============================================================================
# Paired Delimiters & Quotation Fast Mask Table
# =============================================================================

PUNCTUATION_MASK_TABLE: dict[int, str] = str.maketrans(
    {
        ".": PUA_PERIOD,
        "!": PUA_EXCLAMATION,
        "?": PUA_QUESTION,
        "\u3002": PUA_CJK_PERIOD,
        "\uff01": PUA_FULLWIDTH_EXCL,
        "\uff1f": PUA_FULLWIDTH_QUEST,
        "\uff0e": PUA_FULLWIDTH_PERIOD,
    }
)


def mask_punctuation(match: re.Match[str]) -> str:
    """Mask sentence-ending punctuation inside matched quoted or bracketed substring."""
    return match.group(0).translate(PUNCTUATION_MASK_TABLE)


def mask_single_quote_punctuation(match: re.Match[str]) -> str:
    """Mask punctuation inside single quotes while preserving standard contractions."""
    return match.group(0).translate(PUNCTUATION_MASK_TABLE)
