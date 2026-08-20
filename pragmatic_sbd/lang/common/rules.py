"""Common language rules, Unicode PUA definitions, lexicons, and compiled regex patterns."""

from __future__ import annotations

import re
import string
from collections.abc import Callable
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Rule:
    """Immutable rule specification containing a compiled regex and replacement template."""

    pattern: re.Pattern[str]
    replacement: str = ""


# =============================================================================
# 1. Unicode Private Use Area (PUA) Sentinel Assignments
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
# 2. Global Fast Unmask Translation Table
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
    """Restore all PUA sentinels back to original text in a single C-level pass.

    Args:
        text: The string containing private use area (PUA) codepoints.

    Returns:
        The string with all sentinel characters restored to their original form.
    """
    return text.translate(UNMASK_TABLE)


# =============================================================================
# 3. Paired Delimiters & Quotation Fast Mask Table
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
    """Mask sentence-ending punctuation inside matched quoted or bracketed substring.

    Args:
        match: The regex match object containing punctuation.

    Returns:
        The matched string with punctuation mapped to PUA sentinels.
    """
    return match.group(0).translate(PUNCTUATION_MASK_TABLE)


def mask_single_quote_punctuation(match: re.Match[str]) -> str:
    """Mask punctuation inside single quotes while preserving standard contractions.

    Args:
        match: The regex match object containing punctuation.

    Returns:
        The matched string with punctuation inside single quotes mapped to sentinels.
    """
    return match.group(0).translate(PUNCTUATION_MASK_TABLE)


# =============================================================================
# 4. Standard Punctuation & Sentence Starters
# =============================================================================

PUNCTUATIONS: frozenset[str] = frozenset({".", "!", "?", "\u3002", "\uff0e", "\uff01", "\uff1f"})

# fmt: off
SENTENCE_STARTERS: frozenset[str] = frozenset({
    "A", "Being", "Did", "For", "He", "How", "However", "I", "In", "It",
    "Millions", "More", "She", "That", "The", "There", "They", "We", "What",
    "When", "Where", "Who", "Why",
})

# =============================================================================
# 5. Standard Abbreviations & Honorifics
# =============================================================================

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

EXCLAMATION_WORDS_REGEX: re.Pattern[str] = re.compile(
    "|".join(re.escape(word) for word in sorted(EXCLAMATION_WORDS, key=len, reverse=True))
)


def mask_exclamation_words(text: str) -> str:
    """Mask exclamation marks within known proper nouns and click consonants."""
    return EXCLAMATION_WORDS_REGEX.sub(
        lambda match: match.group(0).replace("!", PUA_EXCLAMATION),
        text,
    )


# =============================================================================
# 6. Boundary & Sentence Extraction Patterns
# =============================================================================

# Matches sentences enclosed in quotes/parens, multi-punctuation runs, or terminating marks
SENTENCE_BOUNDARY_REGEX = re.compile(
    r"（(?:[^）])*）(?=\s?[A-Z])|"
    r"「(?:[^」])*」(?=\s[A-Z])|"
    r"\((?:[^\)]){2,}\)(?=\s[A-Z])|"
    r"\'(?:[^\'])*[^,]\'(?=\s[A-Z])|"
    r"\"(?:[^\"])*[^,]\"(?=\s[A-Z])|"
    r"\“(?:[^\”])*[^,]\”(?=\s[A-Z])|"
    r"[\u3002\uff0e.\uff01!?\uff1f ]{2,}|"
    rf"\S.*?[.\u3002\uff0e\uff01!?\uff1f{PUA_TEMP_END_PUNCT}{PUA_NEWLINE}"
    rf"{PUA_DOUBLE_QE}{PUA_DOUBLE_EQ}{PUA_DOUBLE_QQ}{PUA_DOUBLE_EE}]|"
    r"[.\u3002\uff0e\uff01!?\uff1f]"
)

QUOTATION_AT_END_OF_SENTENCE_REGEX = re.compile(
    rf"""[!?.\-{PUA_PERIOD}{PUA_EXCLAMATION}{PUA_QUESTION}]["“”]\s[A-Z]"""
)
SPLIT_SPACE_QUOTATION_AT_END_OF_SENTENCE_REGEX = re.compile(
    rf"""(?<=[!?.\-{PUA_PERIOD}{PUA_EXCLAMATION}{PUA_QUESTION}]["“”])\s(?=[A-Z])"""
)
PARENS_BETWEEN_DOUBLE_QUOTES_REGEX = re.compile(r'["”]\s\([^)]*\)\s["“]')
CONTINUOUS_PUNCTUATION_REGEX = re.compile(r"(?<=\S)([!?]{3,})(?=(\s|\Z|$))")
MULTI_PERIOD_DEFAULT_REGEX = re.compile(
    r"\b[a-zA-Z\u0400-\u0500](?:\.[a-zA-Z\u0400-\u0500])+\.", re.IGNORECASE
)

# Footnote / numbered references (e.g. "end of text.12 Next sentence", "martyr.[1]")
NUMBERED_REFERENCE_REGEX = re.compile(
    rf"(?<=[^\d\s])(?:\.|{PUA_PERIOD})"
    r"(?P<ref>(?:\[(?:\d{1,3},?\s?-?\s?)*\b\d{1,3}\])+|(?:(?:\d{1,3}\s?)?\d{1,3}))"
    r"(?P<space>\s*)(?=(?:[A-Z]|\Z|$))"
)


# =============================================================================
# 7. Pre-Compiled Transformation Rules
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
    # Protect periods in alphanumeric words/emails (e.g. site.com)
    Rule(re.compile(r"([a-zA-Z0-9_])\.([a-zA-Z0-9_])"), r"\g<1>" + PUA_PERIOD + r"\g<2>"),
)

DOUBLE_PUNCTUATION_RULES: tuple[Rule, ...] = (
    Rule(re.compile(r"\?!"), PUA_DOUBLE_QE),
    Rule(re.compile(r"!\?"), PUA_DOUBLE_EQ),
    Rule(re.compile(r"\?\?"), PUA_DOUBLE_QQ),
    Rule(re.compile(r"!!"), PUA_DOUBLE_EE),
)

ELLIPSIS_RULES: tuple[Rule, ...] = (
    Rule(
        re.compile(r"(\s\.){3}\s"),
        (PUA_ELLIPSIS_SPACE + PUA_ELLIPSIS_DOT) * 3 + PUA_ELLIPSIS_SPACE,
    ),
    Rule(
        re.compile(r"(?<=[a-z])(\.\s){3}\.(?=$|\n)"),
        (PUA_ELLIPSIS_DOT + PUA_ELLIPSIS_SPACE) * 3 + PUA_ELLIPSIS_DOT,
    ),
    Rule(
        re.compile(r"(?<=\S)\.{3}(?=\.\s[A-Z])"),
        PUA_ELLIPSIS_DOT * 3,
    ),
    Rule(
        re.compile(r"\.\.\.(?=\s+[A-Z])"),
        PUA_ELLIPSIS_DOT * 2 + ".",
    ),
    Rule(
        re.compile(r"\.\.\."),
        PUA_ELLIPSIS_DOT * 3,
    ),
)

# Consolidates leading numbers, decimals, and list enumerators (1., 12., 999.)
NUMBER_RULES: tuple[Rule, ...] = (
    Rule(re.compile(r"\.(?=\d)"), PUA_PERIOD),
    Rule(re.compile(r"(?<=\d)\.(?=\S)"), PUA_PERIOD),
    Rule(
        re.compile(rf"((?:(?<=^)|(?<=[\r\n{PUA_NEWLINE}]))\d{{1,3}})\.(?=\s\S|\))"),
        r"\g<1>" + PUA_PERIOD,
    ),
)

# Unmasks terminal period in a.m. / p.m. ONLY when it ends a sentence before a capitalized word
AM_PM_RULES: tuple[Rule, ...] = (
    Rule(
        re.compile(rf"(?<=\b[AaPp]{PUA_PERIOD}[Mm]){PUA_PERIOD}(?=\s[A-Z])"),
        ".",
    ),
)


# =============================================================================
# 8. Paired Delimiters & Quotation Regexes
# =============================================================================

BETWEEN_DOUBLE_QUOTES_REGEX: re.Pattern[str] = re.compile(
    r'"(?=(?P<tmp_dq>[^"\r\n\\]+|\\{2}|\\.)*)(?P=tmp_dq)"'
)
BETWEEN_QUOTE_ARROW_REGEX: re.Pattern[str] = re.compile(
    r"\u00ab(?=(?P<tmp_arr>[^\u00bb\r\n\\]+|\\{2}|\\.)*)(?P=tmp_arr)\u00bb"
)
BETWEEN_QUOTE_SLANTED_REGEX: re.Pattern[str] = re.compile(
    r"\u201c(?=(?P<tmp_sq>[^\u201d\r\n\\]+|\\{2}|\\.)*)(?P=tmp_sq)\u201d"
)
BETWEEN_SQUARE_BRACKETS_REGEX: re.Pattern[str] = re.compile(
    r"\[(?=(?P<tmp_sb>[^\]\r\n\\]+|\\{2}|\\.)*)(?P=tmp_sb)\]"
)
BETWEEN_PARENS_REGEX: re.Pattern[str] = re.compile(r"\((?=(?P<tmp_p>[^()\r\n\\]+|\\{2}|\\.)*)(?P=tmp_p)\)")
BETWEEN_SINGLE_QUOTES_REGEX: re.Pattern[str] = re.compile(
    r"(?:(?<=^)|(?<=\s))'(?!\s)(?:[^'\n\r]|(?<=[a-zA-Z])'(?=[a-zA-Z]))+?'(?=[\s.,!?;:\)\]\n\r]|$)"
)
BETWEEN_SINGLE_QUOTE_SLANTED_REGEX: re.Pattern[str] = re.compile(
    r"(?:(?<=^)|(?<=\s))\u2018(?!\s)(?:[^\u2019\n\r]|(?<=[a-zA-Z])\u2019(?=[a-zA-Z]))+?\u2019(?=[\s.,!?;:\)\]\n\r]|$)"
)
BETWEEN_EM_DASHES_REGEX: re.Pattern[str] = re.compile(r"--(?=(?P<tmp_ed>[^-\r\n]*))(?P=tmp_ed)--")
WORD_WITH_LEADING_APOSTROPHE: re.Pattern[str] = re.compile(r"(?<=\s)'(?:[^']|'[a-zA-Z])*'\S")

STANDARD_PAIRED_PATTERNS: tuple[tuple[re.Pattern[str], Callable[[re.Match[str]], str]], ...] = (
    (BETWEEN_DOUBLE_QUOTES_REGEX, mask_punctuation),
    (BETWEEN_QUOTE_ARROW_REGEX, mask_punctuation),
    (BETWEEN_QUOTE_SLANTED_REGEX, mask_punctuation),
    (BETWEEN_SQUARE_BRACKETS_REGEX, mask_punctuation),
    (BETWEEN_PARENS_REGEX, mask_punctuation),
    (BETWEEN_SINGLE_QUOTE_SLANTED_REGEX, mask_punctuation),
    (BETWEEN_EM_DASHES_REGEX, mask_punctuation),
)


# =============================================================================
# 9. List Item Regexes
# =============================================================================

NUMBER_LIST_REGEX: re.Pattern[str] = re.compile(
    r"(?P<lead>(?:^|[\r\n]|\s)(?:[•⁃\-]\s*)?)"
    r"(?:(?P<lparen>\()(?P<num_p>\d{1,3})\)|(?P<num>\d{1,3})(?P<delim>\.\)?|\)))(?=\s|$)"
)
ALPHA_LIST_REGEX: re.Pattern[str] = re.compile(
    r"(?P<lead>(?:^|[\r\n]|\s)(?:[•⁃\-]\s*)?)"
    r"(?:(?P<lparen>\()(?P<letter_p>[a-z])\)|(?P<letter>[a-z])(?P<delim>\.\)?|\)))(?=\s|$)"
)
ROMAN_PARENS_REGEX: re.Pattern[str] = re.compile(
    r"(?P<lead>(?:^|[\r\n]|\s)(?:[•⁃\-]\s*)?)\((?P<roman>[ivxldcm]+)\)(?=\s|$)",
    re.IGNORECASE,
)
ROMAN_DELIM_REGEX: re.Pattern[str] = re.compile(
    r"(?P<lead>(?:^|[\r\n]|\s)(?:[•⁃\-]\s*)?)(?P<roman>[ivxldcm]+)(?P<delim>\.\)?|\))(?=\s|$)",
    re.IGNORECASE,
)


# =============================================================================
# 10. Abbreviation Regexes
# =============================================================================

POSSESSIVE_ABBR_REGEX: re.Pattern[str] = re.compile(r"\.(?='s\b|’s\b|'S\b|’S\b)")
KOMMANDITGESELLSCHAFT_REGEX: re.Pattern[str] = re.compile(
    r"(?<=Co)\.(?=\s*(?:KG|GmbH|OHG|AG)\b)", re.IGNORECASE
)
SINGLE_UPPERCASE_LETTER_REGEX: re.Pattern[str] = re.compile(
    r"((?:(?<=^)|(?<=[\s\ue000]))[A-ZА-ЯЁ])\.(?=[,.:\-?!]|\s|[A-ZА-ЯЁ]\.|\s*$)"
)
SINGLE_LOWERCASE_LETTER_REGEX: re.Pattern[str] = re.compile(
    r"((?:(?<=^)|(?<=\s))[a-zа-яё])\.(?=\s+[a-zA-Zа-яёА-ЯЁ]|\s*$)"
)
AM_PM_REGEX: re.Pattern[str] = re.compile(r"(?<=\d)\s*(?:a\.m|p\.m|am|pm)\b", re.IGNORECASE)

ROMAN_NUMERALS: dict[str, int] = {
    roman: index
    for index, roman in enumerate(
        (
            "i", "ii", "iii", "iv", "v", "vi", "vii", "viii", "ix", "x",
            "xi", "xii", "xiii", "xiv", "xv", "xvi", "xvii", "xviii", "xix", "xx",
        )
    )
}
ROMAN_NUMERALS_SET: frozenset[str] = frozenset(ROMAN_NUMERALS.keys())
LATIN_NUMERALS: dict[str, int] = {char: index for index, char in enumerate(string.ascii_lowercase)}
