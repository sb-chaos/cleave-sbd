import re

from .common import PUA_PERIOD, Rule

ISO_CODE = "ru"

SENTENCE_STARTERS: frozenset[str] = frozenset()
PREPOSITIVE_ABBREVIATIONS: frozenset[str] = frozenset()
NUMBER_ABBREVIATIONS: frozenset[str] = frozenset()
REPLACE_ALL_ABBR_PERIODS = True

MULTI_PERIOD_ABBREVIATION_REGEX = re.compile(r"\b[\u0400-\u04FF]+(?:\.[\u0400-\u04FF]+)+[.]?", re.IGNORECASE)

# fmt: off
# Deduplicated Russian Abbreviations
ABBREVIATIONS: frozenset[str] = frozenset({
    "y", "y.e", "а", "авт", "адм.-терр", "акад", "в", "вв", "вкз",
    "вост.-европ", "г", "гг", "гос", "гр", "д", "деп", "дисс", "дол",
    "долл", "ежедн", "ж", "жен", "з", "зап", "зап.-европ", "заруб",
    "и", "ин", "иностр", "инст", "к", "канд", "кв", "кг", "куб", "л",
    "л.h", "л.н", "м", "мин", "моск", "муж", "н", "нед", "о", "п",
    "пгт", "пер", "пп", "пр", "просп", "проф", "р", "руб", "с", "сек",
    "см", "спб", "стр", "т", "тел", "тов", "тт", "тыс", "у", "у.е",
    "ул", "ф", "ч",
})
# fmt: on

# Language-specific replacement rules
RULES: tuple[Rule, ...] = (
    # Cyrillic single-letter initials at line start or mid-sentence (e.g. " А. ")
    Rule(re.compile(r"((?:(?<=^)|(?<=\s))[А-ЯЁ])\.(?=\s)"), r"\g<1>" + PUA_PERIOD),
)
