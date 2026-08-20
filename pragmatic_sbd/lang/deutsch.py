"""German (Deutsch) language configuration for sentence boundary disambiguation.

Includes German sentence starters, month ordinal date protection (e.g., '1. Januar'),
German-style quotation marks („ ... “ and ,, ... “), and abbreviation lexicons.
"""

import re

from .common.standard import PUA_PERIOD, Rule

ISO_CODE = "de"

MONTHS: tuple[str, ...] = (
    "Januar",
    "Februar",
    "März",
    "April",
    "Mai",
    "Juni",
    "Juli",
    "August",
    "September",
    "Oktober",
    "November",
    "Dezember",
)

# fmt: off
SENTENCE_STARTERS: frozenset[str] = frozenset({
    "Am", "Auch", "Auf", "Bei", "Da", "Das", "Der", "Die", "Ein", "Eine",
    "Es", "Für", "Heute", "Ich", "Im", "In", "Ist", "Jetzt", "Mein", "Mit",
    "Nach", "So", "Und", "Warum", "Was", "Wenn", "Wer", "Wie", "Wir",
})
# fmt: on

NUMBER_ABBREVIATIONS: frozenset[str] = frozenset({"art", "ca", "no", "nos", "nr", "pp"})

PREPOSITIVE_ABBREVIATIONS: frozenset[str] = frozenset()

# fmt: off
# German Abbreviations (cleaned of trailing whitespace artifacts)
ABBREVIATIONS: frozenset[str] = frozenset({
    "ä", "adj", "adm", "adv", "ao.univ.prof", "art", "ass", "ass.prof",
    "asst", "b.a", "b.s", "bart", "bldg", "brig", "bros", "bse", "buchst",
    "bzgl", "bzw", "c.-à-d", "ca", "capt", "chr", "cmdr", "co", "col",
    "comdr", "con", "corp", "cpl", "d.h", "d.j", "dergl", "dgl", "di",
    "dipl.-ing", "dkr", "dr", "ens", "etc", "ev", "evtl", "ff", "g.g.a",
    "g.u", "gen", "ggf", "gov", "hon", "hon.prof", "hosp", "i.f", "i.h.v",
    "ii", "iii", "insp", "iv", "ix", "jun", "k.o", "kath", "lfd", "lt",
    "ltd", "m.e", "mag", "maj", "med", "messrs", "mio", "mlle", "mm",
    "mme", "mr", "mrd", "mrs", "ms", "msgr", "mwst", "no", "nos", "nr",
    "o.ä", "o.univ.-prof", "op", "ord", "pfc", "ph", "pp", "prof",
    "projektass", "pvt", "rep", "reps", "res", "rev", "rt", "s.p.a",
    "sa", "sen", "sens", "sfc", "sgt", "sog", "sogen", "spp", "sr", "st",
    "std", "str", "stud.ass", "supt", "surg", "u.a", "u.e", "u.s.w",
    "u.u", "u.ä", "univ.-doz", "univ.-prof", "univ.ass", "usf", "usw",
    "v", "vgl", "vi", "vii", "viii", "vs", "x", "xi", "xii", "xiii",
    "xiv", "xix", "xv", "xvi", "xvii", "xviii", "xx", "z.b", "z.t",
    "z.z", "z.zt", "zt", "zzt",
})
# fmt: on

# German Quotation Pair Patterns (Low-9 / High-66 & Informal Double Commas)
GERMAN_DOUBLE_QUOTES_REGEX = re.compile(r"\u201e(?=(?P<tmp>[^\u201c\\]+|\\{2}|\\.)*)(?P=tmp)\u201c")
GERMAN_UNCONVENTIONAL_QUOTES_REGEX = re.compile(r",,(?=(?P<tmp>[^\u201c\\]+|\\{2}|\\.)*)(?P=tmp)\u201c")

PAIRED_PUNCTUATION_PATTERNS: tuple[re.Pattern[str], ...] = (
    GERMAN_DOUBLE_QUOTES_REGEX,
    GERMAN_UNCONVENTIONAL_QUOTES_REGEX,
)

# Consolidated Regex for German Dates: e.g. "1. Januar", "24. Dezember"
_MONTHS_PATTERN = "|".join(MONTHS)
GERMAN_DATE_REGEX = re.compile(rf"(?<=\d)\.(?=\s*(?:{_MONTHS_PATTERN}))")

# Language-specific transformation rules
RULES: tuple[Rule, ...] = (
    # German ordinal dates (e.g. "1. Januar")
    Rule(GERMAN_DATE_REGEX, PUA_PERIOD),
    # Positive and negative ordinal numbers (e.g. " 1. ", " 12. ", " -5. ")
    Rule(re.compile(r"((?:(?<=^)|(?<=\s))-?\d{1,2})\.(?=\s)"), rf"\1{PUA_PERIOD}"),
    # Single lower-case initials at line start or mid-sentence (e.g. " z. B. ")
    Rule(re.compile(r"((?:(?<=^)|(?<=\s))[a-z])\.(?=\s)"), rf"\1{PUA_PERIOD}"),
)
