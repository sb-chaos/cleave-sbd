"""Kazakh (Қазақша) language configuration for sentence boundary disambiguation.

Handles Cyrillic script abbreviations, multi-period acronyms, single-letter initials,
and dialogue dashes following question or exclamation marks.
"""

import re

from .common.standard import (
    PUA_EXCLAMATION,
    PUA_PERIOD,
    PUA_QUESTION,
    Rule,
)

ISO_CODE = "kk"

SENTENCE_STARTERS: frozenset[str] = frozenset()
PREPOSITIVE_ABBREVIATIONS: frozenset[str] = frozenset()
NUMBER_ABBREVIATIONS: frozenset[str] = frozenset()

# fmt: off
# Deduplicated Kazakh (Cyrillic and Latin) Abbreviations
ABBREVIATIONS: frozenset[str] = frozenset({
    "aбб", "afp", "anp", "atp", "bae", "bg", "bp", "cam", "cctv", "cd",
    "cez", "cgi", "cnpc", "dvd", "eiti", "epo", "er", "farc", "fbi", "gp",
    "gps", "has", "hiv", "hrh", "http", "icu", "idf", "imd", "ime", "ip",
    "iso", "kaz", "kpa", "kpo", "kz", "mgm", "mri", "nasa", "nba", "nbc",
    "nds", "ohl", "omlt", "pda", "pkk", "ppm", "psm", "psp", "raf", "rss",
    "rtl", "sas", "sme", "sms", "tnt", "udf", "uefa", "usb", "utc", "x",
    "zdf", "а.", "аақ", "авг.", "аек", "акад.", "ак", "акср", "акцион.",
    "амт", "англ", "апр", "апр.", "аум.", "аф", "ацат", "ақ", "ақш",
    "аөсшк", "б. з. б.", "б. з. д.", "б. т.", "б. э. д.", "б.б.", "ббс",
    "биікт.", "биол.", "биохим", "бмтрк", "боак", "бсн", "бта", "бхооо",
    "бұұ", "бө", "вич", "всоонл", "г", "геогр.", "геол.", "гленкор",
    "гсбп", "гсдп", "гулаг", "гэс", "дек.", "дк", "днқ", "дсұ", "еақк",
    "еаэы", "еқыұ", "ембімұнайгаз", "ео", "еуразэқ", "еуроодақ", "еұу",
    "еэы", "ж.", "жж.", "жіө", "жко", "жоо", "жкт", "жққ", "жсдп", "жск",
    "жтсх", "жхл", "жшс", "жэк", "зоо", "и.", "инта", "исаф", "іім",
    "камаз", "кг", "кгб", "кеу", "кимеп", "км", "км²", "км³", "кмс",
    "кокп", "кота", "кср", "ксро", "кту", "кхдр", "қазатомпром", "қазкср",
    "қазмұнайгаз", "қазпошта", "қазтаг", "қазұу", "қк", "қкп", "қмдб",
    "ққс", "қр", "қхр", "қ.", "лат.", "м", "м.", "м²", "м³", "магатэ",
    "маж", "май.", "максам", "мб", "мбф", "мвт", "мемдум", "мемл", "мин",
    "млн", "млрд", "мм", "мм.", "мқо", "мр", "мсоп", "мт", "мтк", "мыс.",
    "наса", "нато", "нквд", "нояб.", "нұсжп", "оар", "обб", "обл.", "огпу",
    "оеб", "окт.", "опек", "оңт.", "өзенмұнайгаз", "өгк", "өұқ", "өф",
    "пед.", "пиқ", "пәк", "р.", "ржмб", "ркфср", "рлдп", "рнқ", "рсфср",
    "ртж", "руб", "рф", "рфкп", "с.", "с.ш.", "сбд", "сбл", "свс", "сву",
    "сду", "сес", "сент.", "см", "снпс", "солт.", "сооно", "спбму", "ссс",
    "ссср", "сср", "ссро", "сэс", "т", "т.", "т. б.", "т. с. с.", "т.с.с",
    "тв", "тереңд.", "тех.", "тим", "тж", "тжқ", "тмд", "тр", "трлн",
    "тэц", "төм.", "уаз", "уефа", "ук", "ұқк", "ұқшұ", "февр.", "фкққ",
    "фсб", "фққ", "хвқ", "хдо", "хдп", "хим.", "хтқо", "хқко", "цас",
    "цтп", "ш.", "ш.б.", "шыұ", "шұар", "экон.", "экспо", "эқк", "эөкк",
    "эыдұ", "юнеско", "янв.", "әқбк", "әөк", "әч", "ғ.", "ғ. с.",
})
# fmt: on

# Cyrillic and Latin multi-period abbreviation pattern
MULTI_PERIOD_ABBREVIATION_REGEX = re.compile(
    r"\b[\u0400-\u0500]+(?:\.\s?[\u0400-\u0500])+[.]|\b[a-z](?:\.[a-z])+[.]"
)

# Language-specific transformation rules
RULES: tuple[Rule, ...] = (
    # Cyrillic single-letter initials at line start or mid-sentence (e.g. " А. ")
    Rule(re.compile(r"((?:(?<=^)|(?<=\s))[А-ЯЁ])\.(?=\s)"), rf"\1{PUA_PERIOD}"),
    # Protect question mark before dialogue dash (e.g. "? —")
    Rule(re.compile(r"\?(?=\s*[-\u2014]\s*)"), PUA_QUESTION),
    # Protect exclamation mark before dialogue dash (e.g. "! —")
    Rule(re.compile(r"!(?=\s*[-\u2014]\s*)"), PUA_EXCLAMATION),
)
