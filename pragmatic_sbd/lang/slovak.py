"""Slovak (Slovenčina) language configuration for sentence boundary disambiguation.

Includes Slovak sentence starters, months (nominative and genitive), ordinal rules,
Roman numeral rules, Slovak low-9/high-66 quotation marks („ ... “), and an extensive
abbreviation lexicon.
"""

import re

from .common.standard import PUA_PERIOD, Rule

ISO_CODE = "sk"

# Slovak Months in both Nominative and Genitive cases
MONTHS: tuple[str, ...] = (
    "Január",
    "Február",
    "Marec",
    "Apríl",
    "Máj",
    "Jún",
    "Júl",
    "August",
    "September",
    "Október",
    "November",
    "December",
    "Januára",
    "Februára",
    "Marca",
    "Apríla",
    "Mája",
    "Júna",
    "Júla",
    "Augusta",
    "Septembra",
    "Októbra",
    "Novembra",
    "Decembra",
)

SENTENCE_STARTERS: frozenset[str] = frozenset()

# fmt: off
NUMBER_ABBREVIATIONS: frozenset[str] = frozenset({
    "no", "nr", "č",
})

PREPOSITIVE_ABBREVIATIONS: frozenset[str] = frozenset({
    "bc", "doc", "dr", "drsc", "ing", "judr", "mgr", "mudr", "p", "prof",
    "st",
})

# Deduplicated Slovak Abbreviations
ABBREVIATIONS: frozenset[str] = frozenset({
    "a. d", "a. g. p", "a. i. i", "a. k. a", "a. m", "a. r. k", "a. s",
    "a. s. a. p", "a. v", "a.d", "a.g.p", "a.i.i", "a.k.a", "a.m", "a.s",
    "a.s.a.p", "a.v", "akad", "al", "apod", "arm", "atd", "atď", "atď.",
    "bc", "bros", "c. k", "c.k", "cca", "co", "corp", "csc", "d. c", "d.c",
    "doc", "dr", "drsc", "e. t", "e.t", "el", "etc", "ev", "gen", "hl",
    "hod", "i. b", "i.b", "ii", "iii", "inc", "ind", "ing", "iv", "jr",
    "judr", "k. o", "k.o", "kol", "konkr", "kt", "ll. m", "ll.m", "m. n. m",
    "m.n.m", "m.o", "max", "mgr", "mil", "min", "mld", "ml", "mr", "mudr",
    "mvdr", "n. a", "n. o", "n. w. a", "n.a", "n.o", "n.w.a", "napr",
    "naprk", "např", "nešp", "no", "nr", "nám", "nár", "o. c. p", "o. f. i",
    "o. k", "o. z", "o.c.p", "o.f.i", "o.i", "o.k", "o.z", "obr", "obv",
    "odd", "ods", "os", "p", "p. a", "p. n. l", "p. s", "p.a", "p.n.l",
    "p.s", "paeddr", "pedg", "ph. d", "ph.d", "phdr", "phd", "plgr", "pod",
    "pok", "pol. pr", "pol.pr", "por", "pozn", "pp", "pr", "prek", "prof",
    "príp", "písm", "r. o", "r.o", "red", "resp", "rndr", "rozh", "roz",
    "rsdr", "rtg", "s. a", "s. e. g", "s. r. o", "s.a", "s.e.g", "s.r.o",
    "skr", "sl", "slov", "soc", "sp", "spol", "sr", "st", "stor", "str",
    "stred", "sv", "súkr", "sz", "t. č", "t. j", "t. z", "t.č", "t.j",
    "t.z", "tel", "tis", "tj", "tr", "tu", "tvz", "tz", "tzn", "tzv",
    "u. s", "u.s", "ul", "v. sp", "v.sp", "var", "vi", "viď", "vs", "vyd",
    "vz", "xx", "z. z", "z.z", "zb", "zdravot", "zs", "zz", "zák", "č",
    "čs", "čsl", "št", "š. p", "š.p", "ú. p. v. o", "ú.p.v.o",
})
# fmt: on

# Slovak Quotation Pair Pattern (Low-9 / High-66)
SLOVAK_DOUBLE_QUOTES_REGEX = re.compile(r"\u201e(?=(?P<tmp>[^\u201c\\]+|\\{2}|\\.)*)(?P=tmp)\u201c")

PAIRED_PUNCTUATION_PATTERNS: tuple[re.Pattern[str], ...] = (SLOVAK_DOUBLE_QUOTES_REGEX,)

# Consolidated Regex for Slovak Dates: e.g. "1. Januára", "24. Decembra"
_MONTHS_PATTERN = "|".join(MONTHS)
SLOVAK_DATE_REGEX = re.compile(rf"(?<=\d)\.(?=\s*(?:{_MONTHS_PATTERN}))")

# Language-specific transformation rules
RULES: tuple[Rule, ...] = (
    # Slovak ordinal dates (e.g. "1. Január", "15. Marca")
    Rule(SLOVAK_DATE_REGEX, PUA_PERIOD),
    # Ordinal numbers followed by lowercase text (e.g. "1. poschodie")
    Rule(re.compile(r"(?<=\d)\.(?=\s*[a-z]+)"), PUA_PERIOD),
    # Roman numeral list items/ordinals (e.g. " IV. ", " X. ")
    Rule(re.compile(r"((?:(?<=^)|(?<=\s))[VXI]+)\.(?=\s+)", re.IGNORECASE), rf"\1{PUA_PERIOD}"),
)
