"""Polish (Polski) language configuration for sentence boundary disambiguation.

Includes standard Polish linguistic, grammatical, and general abbreviations.
"""

from .common.standard import Rule

ISO_CODE = "pl"

SENTENCE_STARTERS: frozenset[str] = frozenset()
PREPOSITIVE_ABBREVIATIONS: frozenset[str] = frozenset()
NUMBER_ABBREVIATIONS: frozenset[str] = frozenset()

# fmt: off
# Deduplicated Polish Abbreviations
ABBREVIATIONS: frozenset[str] = frozenset({
    "I cont", "R cont", "ags", "alb", "ang", "aor", "awest", "bałt", "bojkow",
    "bret", "brus", "bsł", "bułg", "c.b.d.o", "c.b.d.u", "celt", "chorw",
    "cs", "czakaw", "czerw", "czes", "dłuż", "dniem", "dor", "dubrow",
    "duń", "ekaw", "fiń", "franc", "gal", "germ", "głuż", "gniem", "goc",
    "gr", "grudz", "hebr", "het", "hol", "ie", "ikaw", "irań", "irl",
    "islandz", "itd", "itd.", "itp", "jekaw", "kajkaw", "kasz", "kirg",
    "kwiec", "lip", "listop", "lit", "lp", "maced", "mar", "moraw",
    "młpol", "n.e", "nb.", "ngr", "niem", "nord", "norw", "np", "np.",
    "ok.", "orm", "oset", "osk", "p.n", "p.n.e", "p.o", "pazdz", "pers",
    "pie", "pod red.", "podhal", "pol", "port", "połab", "prekm", "pskow",
    "psł", "rez", "rom", "rozdz.", "rum", "rus", "rys.", "sas", "sch",
    "scs", "serb", "sierp", "sp. z o.o", "stbułg", "stind", "stpol", "stpr",
    "str.", "strus", "stwniem", "stycz", "sztokaw", "szwedz", "sła", "słe",
    "słi", "słow", "t.", "tj.", "toch", "tur", "tzn", "tłum.", "ukr", "ul",
    "umbr", "wed", "wlkpol", "wrzes", "wyd.", "włos", "węg", "zakarp", "łot",
    "łac", "śl", "śrdniem", "śrgniem", "śrirl",
})
# fmt: on

# Language-specific replacement rules
RULES: tuple[Rule, ...] = ()
