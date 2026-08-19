"""Bulgarian language configuration for sentence boundary disambiguation."""

from .common.standard import Rule

ISO_CODE = "bg"

SENTENCE_STARTERS: frozenset[str] = frozenset()
PREPOSITIVE_ABBREVIATIONS: frozenset[str] = frozenset()
NUMBER_ABBREVIATIONS: frozenset[str] = frozenset()

# fmt: off
# Cyrillic and Latin Abbreviations
ABBREVIATIONS: frozenset[str] = frozenset({
    "p.s", "акад", "ал", "б.р", "б.ред", "бел.а", "бел.пр", "бр", "бул",
    "в", "вж", "вкл", "вм", "вр", "г", "ген", "гр", "дж", "дм", "доц",
    "др", "ем", "заб", "зам", "инж", "к.с", "кв", "кв.м", "кг", "км",
    "кор", "куб", "куб.м", "л", "лв", "м", "м.г", "мин", "млн", "млрд",
    "мм", "н.с", "напр", "пл", "полк", "проф", "р", "рис", "с", "св",
    "сек", "см", "сп", "срв", "ст", "стр", "т", "т.г", "т.е", "т.н",
    "т.нар", "табл", "тел", "у", "ул", "фиг", "ха", "хил", "ч", "чл",
    "щ.д",
})
# fmt: on

# Language-specific replacement rules
RULES: tuple[Rule, ...] = ()
