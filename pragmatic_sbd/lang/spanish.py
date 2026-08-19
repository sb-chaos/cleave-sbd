"""Spanish (Español) language configuration for sentence boundary disambiguation.

Includes standard Spanish abbreviations, titles, prefixes, and numeric reference terms.
"""

from .common.standard import Rule

ISO_CODE = "es"

SENTENCE_STARTERS: frozenset[str] = frozenset()

NUMBER_ABBREVIATIONS: frozenset[str] = frozenset(
    {
        "cra",
        "ext",
        "no",
        "nos",
        "p",
        "pp",
        "tel",
    }
)

# fmt: off
# Deduplicated Spanish Prepositive Abbreviations and Prefixes
PREPOSITIVE_ABBREVIATIONS: frozenset[str] = frozenset({
    "a", "aero", "ambi", "an", "anfi", "ante", "anti", "archi", "arci", "auto",
    "bi", "bien", "bis", "co", "com", "con", "contra", "crio", "cuadri",
    "cuasi", "cuatri", "de", "deci", "des", "di", "dis", "dr", "ecto", "ee",
    "en", "endo", "entre", "epi", "equi", "ex", "extra", "geo", "hemi",
    "hetero", "hiper", "hipo", "homo", "i", "im", "in", "infra", "inter",
    "intra", "iso", "lic", "macro", "mega", "micro", "mini", "mono", "mt",
    "multi", "neo", "omni", "para", "pen", "ph", "ph.d", "pluri", "poli",
    "pos", "post", "pre", "pro", "prof", "pseudo", "re", "retro", "semi",
    "seudo", "sobre", "sra", "srta", "sub", "super", "supra", "trans", "tras",
    "tri", "ulter", "ultra", "un", "uni", "vice", "yuxta",
})

# Deduplicated Spanish Abbreviations Lexicon
ABBREVIATIONS: frozenset[str] = frozenset({
    "a", "a.c", "a/c", "abr", "adj", "admón", "aero", "afmo", "ago", "almte",
    "ambi", "an", "anfi", "ante", "anti", "ap", "apdo", "archi", "arci", "arq",
    "art", "atte", "auto", "av", "avda", "bco", "bi", "bibl", "bien", "bis",
    "bs. as", "c", "c.f", "c.g", "c/c", "c/u", "cap", "cc.aa", "cdad", "cm",
    "co", "com", "con", "contra", "cra", "crio", "cta", "cuadri", "cuasi",
    "cuatri", "cv", "d.e.p", "da", "dcha", "dcho", "de", "deci", "dep", "des",
    "di", "dic", "dicc", "dir", "dis", "dn", "doc", "dom", "dpto", "dr", "dra",
    "dto", "ecto", "ee", "ej", "en", "endo", "entlo", "entre", "epi", "equi",
    "esq", "etc", "ex", "excmo", "ext", "extra", "f.c", "fca", "fdo", "febr",
    "ff. aa", "ff.cc", "fig", "fil", "fra", "g.p", "g/p", "geo", "gob", "gr",
    "gral", "grs", "hemi", "hetero", "hiper", "hipo", "hnos", "homo", "hs",
    "i", "igl", "iltre", "im", "imp", "impr", "impto", "in", "incl", "infra",
    "ing", "inst", "inter", "intra", "iso", "izdo", "izq", "izqdo", "j.c",
    "jue", "jul", "jun", "kg", "km", "lcdo", "ldo", "let", "lic", "ltd", "lun",
    "macro", "mar", "may", "mega", "mg", "micro", "min", "mini", "mié", "mm",
    "mono", "mt", "multi", "máx", "mín", "n. del t", "n.b", "neo", "no", "nov",
    "ntra. sra", "núm", "oct", "omni", "p", "p.a", "p.d", "p.ej", "p.v.p",
    "para", "pen", "ph", "ph.d", "pluri", "poli", "pos", "post", "ppal", "pre",
    "prev", "pro", "prof", "prov", "pseudo", "ptas", "pts", "pza", "pág",
    "págs", "párr", "párrf", "q.e.g.e", "q.e.p.d", "q.e.s.m", "re", "reg",
    "rep", "retro", "rr. hh", "rte", "s", "s. a", "s.a.r", "s.e", "s.l",
    "s.r.c", "s.r.l", "s.s.s", "s/n", "sdad", "seg", "semi", "sept", "seudo",
    "sig", "sobre", "sr", "sra", "sres", "srta", "sta", "sto", "sub", "super",
    "supra", "sáb", "t.v.e", "tamb", "tel", "tfno", "trans", "tras", "tri",
    "ud", "uds", "ulter", "ultra", "un", "uni", "univ", "uu", "v.b", "v.e",
    "vd", "vds", "vice", "vid", "vie", "vol", "vs", "vto", "yuxta",
})
# fmt: on

# Language-specific replacement rules
RULES: tuple[Rule, ...] = ()
