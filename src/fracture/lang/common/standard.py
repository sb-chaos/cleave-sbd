"""Standard rules, abbreviations, and PUA-masked token definitions.

Replaces arbitrary multi-character / esoteric unicode symbols with dedicated
Unicode Private Use Area (PUA) codepoints (\ue000 - \ue024) to guarantee:
1. 1:1 character length invariance (spans and offsets stay exact).
2. O(1) set-based abbreviation lookups.
3. C-speed string unmasking via str.translate with zero regex overhead.
"""

import re
from typing import NamedTuple


class Rule(NamedTuple):
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
PUA_TEMP_END_PUNCT = "\ue00b"  # Temporary boundary marker (formerly ȸ)
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
# Standard Vocabulary & Abbreviations
# =============================================================================

PUNCTUATIONS: frozenset[str] = frozenset({".", "!", "?", "\u3002", "\uff0e", "\uff01", "\uff1f"})

# fmt: off
SENTENCE_STARTERS: frozenset[str] = frozenset({
    "A", "Being", "Did", "For", "He", "How", "However", "I", "In", "It",
    "Millions", "More", "She", "That", "The", "There", "They", "We", "What",
    "When", "Where", "Who", "Why",
})

STANDARD_ABBREVIATIONS: frozenset[str] = frozenset({
    "adj", "adm", "adv", "al", "ala", "alta", "apr", "arc", "ariz", "ark",
    "art", "assn", "asst", "attys", "aug", "ave", "bart", "bld", "bldg",
    "blvd", "brig", "bros", "btw", "cal", "calif", "capt", "cl", "cmdr",
    "co", "col", "colo", "comdr", "con", "conn", "corp", "cpl", "cres",
    "ct", "d.phil", "dak", "dec", "del", "dept", "det", "dist", "dr",
    "dr.phil", "dr.philos", "drs", "e.g", "ens", "esp", "esq", "etc",
    "exp", "expy", "ext", "feb", "fed", "fig", "fla", "ft", "fwy", "fy",
    "ga", "gen", "gov", "hon", "hosp", "hr", "hway", "hwy", "i.e", "ia",
    "id", "ida", "ill", "inc", "ind", "ing", "insp", "is", "jan", "jr",
    "jul", "jun", "kan", "kans", "ken", "ky", "la", "lt", "ltd", "maj",
    "man", "mar", "mass", "may", "md", "me", "med", "messrs", "mex",
    "mfg", "mich", "min", "minn", "miss", "mlle", "mm", "mme", "mo",
    "mont", "mr", "mrs", "ms", "msgr", "mssrs", "mt", "mtn", "neb",
    "nebr", "nev", "no", "nos", "nov", "nr", "oct", "ok", "okla", "ont",
    "op", "ord", "ore", "p", "pa", "pd", "pde", "penn", "penna", "pfc",
    "ph", "ph.d", "pl", "plz", "pp", "prof", "pvt", "que", "rd", "ref",
    "rep", "reps", "res", "rev", "rs", "rt", "sask", "sec", "sen",
    "sens", "sep", "sept", "sfc", "sgt", "sr", "st", "supt", "surg",
    "tce", "tenn", "tex", "u.s", "univ", "usafa", "ut", "v", "va",
    "ver", "viz", "vs", "vt", "wash", "wis", "wisc", "wy", "wyo", "yuk",
})

PREPOSITIVE_ABBREVIATIONS: frozenset[str] = frozenset({
    "adm", "attys", "brig", "capt", "cmdr", "col", "cpl", "det", "dr",
    "fig", "gen", "gov", "ing", "lt", "maj", "messrs", "mr", "mrs", "ms",
    "msgr", "mssrs", "mt", "ph", "prof", "rep", "reps", "rev", "sen",
    "sens", "sgt", "st", "supt", "v", "vs",
})

NUMBER_ABBREVIATIONS: frozenset[str] = frozenset({
    "art", "ext", "no", "nos", "p", "pp",
})
# fmt: on


# =============================================================================
# Pre-Compiled Rules
# =============================================================================

COMMON_RULES: tuple[Rule, ...] = (
    # Protect coordinates like 45°N. 123°W
    Rule(re.compile(r"(?<=[a-zA-Z]°)\.(?=\s*\d+)"), PUA_PERIOD),
    # Protect common file extensions
    Rule(
        re.compile(
            r"(?<=\s)\.(?=(?:jpe?g|png|gif|tiff?|pdf|ps|docx?|xlsx?|svg|bmp|"
            r"tga|exif|odt|html?|txt|rtf|bat|sxw|xml|zip|exe|msi|blend|wmv|"
            r"mp[34]|pptx?|flac|rb|cpp|cs|js)\s)"
        ),
        PUA_PERIOD,
    ),
    # Preserve isolated single newlines
    Rule(re.compile(r"\n"), PUA_NEWLINE),
    # Protect questions/exclamations inside quotes
    Rule(re.compile(r"""\?(?=['"])"""), PUA_QUESTION),
    Rule(re.compile(r"""!(?=['"])"""), PUA_EXCLAMATION),
    # Protect mid-sentence exclamation points
    Rule(re.compile(r"!(?=,\s[a-z])"), PUA_EXCLAMATION),
    Rule(re.compile(r"!(?=\s[a-z])"), PUA_EXCLAMATION),
    # Normalize excessive spacing
    Rule(re.compile(r"\s{3,}"), " "),
    # Protect periods in alphanumeric words/emails (e.g. site.com)
    Rule(re.compile(r"([a-zA-Z0-9_])\.([a-zA-Z0-9_])"), rf"\1{PUA_PERIOD}\2"),
)

DOUBLE_PUNCTUATION_RULES: tuple[Rule, ...] = (
    Rule(re.compile(r"\?!"), PUA_DOUBLE_QE),
    Rule(re.compile(r"!\?"), PUA_DOUBLE_EQ),
    Rule(re.compile(r"\?\?"), PUA_DOUBLE_QQ),
    Rule(re.compile(r"!!"), PUA_DOUBLE_EE),
)

# Ellipsis masking preserves identical character length using PUA repeats
ELLIPSIS_RULES: tuple[Rule, ...] = (
    # Spaced ellipsis: " . . . " (7 chars) -> PUA equivalent (7 chars)
    Rule(
        re.compile(r"(\s\.){3}\s"),
        (PUA_ELLIPSIS_SPACE + PUA_ELLIPSIS_DOT) * 3 + PUA_ELLIPSIS_SPACE,
    ),
    # Trailing spaced ellipsis: ". . . ." (7 chars) -> PUA equivalent (7 chars)
    Rule(
        re.compile(r"(?<=[a-z])(\.\s){3}\.(?=$|\n)"),
        (PUA_ELLIPSIS_DOT + PUA_ELLIPSIS_SPACE) * 3 + PUA_ELLIPSIS_DOT,
    ),
    # 4 consecutive periods before uppercase
    Rule(
        re.compile(r"(?<=\S)\.{3}(?=\.\s[A-Z])"),
        PUA_ELLIPSIS_DOT * 3,
    ),
    # 3 consecutive periods before uppercase (leaves terminal period)
    Rule(
        re.compile(r"\.\.\.(?=\s+[A-Z])"),
        PUA_ELLIPSIS_DOT * 2 + ".",
    ),
    # Any other 3 consecutive periods
    Rule(
        re.compile(r"\.\.\."),
        PUA_ELLIPSIS_DOT * 3,
    ),
)
