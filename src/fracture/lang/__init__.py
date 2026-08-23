"""Language configuration and dynamic loader for Pragmatic SBD."""

from __future__ import annotations

import importlib.resources
import re
import tomllib
from dataclasses import dataclass
from types import ModuleType

from fracture.lang.common import Rule

SUPPORTED_LANGUAGES: frozenset[str] = frozenset(
    {
        "am",
        "ar",
        "bg",
        "da",
        "de",
        "el",
        "en",
        "es",
        "fa",
        "fr",
        "hy",
        "hi",
        "it",
        "ja",
        "kk",
        "mr",
        "my",
        "nl",
        "pl",
        "ru",
        "sk",
        "ur",
        "zh",
    }
)


@dataclass(slots=True, frozen=True)
class LanguageConfig:
    """Read-only container for language-specific SBD rules and lexicons."""

    iso_code: str
    abbreviations: frozenset[str] = frozenset()
    prepositive_abbreviations: frozenset[str] = frozenset()
    number_abbreviations: frozenset[str] = frozenset()
    sentence_starters: frozenset[str] = frozenset()
    punctuations: frozenset[str] | None = None
    sentence_boundary_regex: re.Pattern[str] | None = None
    replace_all_abbr_periods: bool = False
    rules: tuple[Rule, ...] = ()
    clean_rules: tuple[Rule, ...] = ()
    paired_punctuation_patterns: tuple[re.Pattern[str], ...] = ()
    multi_period_abbreviation_regex: re.Pattern[str] | None = None


# Cache parsed configurations to prevent repeated file I/O
_LANGUAGES_CACHE: dict[str, LanguageConfig] = {}


def load_language_config(code: str) -> LanguageConfig:
    """Lazily load, parse, and compile the requested language TOML file."""
    if code in _LANGUAGES_CACHE:
        return _LANGUAGES_CACHE[code]

    if code not in SUPPORTED_LANGUAGES:
        raise ValueError(
            f"Provide valid language ID i.e. ISO code. Supported codes are: {sorted(SUPPORTED_LANGUAGES)}"
        )

    # Resolve, read, and load TOML config using stdlib resources
    ref = importlib.resources.files("fracture.lang.configs").joinpath(f"{code}.toml")
    data = tomllib.loads(ref.read_text(encoding="utf-8"))

    # Instantiate the configuration container
    iso_code = data["iso_code"]
    abbreviations = frozenset(data.get("abbreviations", []))
    prepositive_abbreviations = frozenset(data.get("prepositive_abbreviations", []))
    number_abbreviations = frozenset(data.get("number_abbreviations", []))
    sentence_starters = frozenset(data.get("sentence_starters", []))
    punctuations = frozenset(data["punctuations"]) if "punctuations" in data else None
    replace_all_abbr_periods = data.get("replace_all_abbr_periods", False)

    sentence_boundary_regex = (
        re.compile(data["sentence_boundary_regex"])
        if "sentence_boundary_regex" in data
        else None
    )

    multi_period_abbreviation_regex = (
        re.compile(data["multi_period_abbreviation_regex"])
        if "multi_period_abbreviation_regex" in data
        else None
    )

    rules = tuple(
        Rule(re.compile(r["pattern"]), r["replacement"]) for r in data.get("rules", [])
    )

    clean_rules = tuple(
        Rule(re.compile(r["pattern"]), r["replacement"])
        for r in data.get("clean_rules", [])
    )

    paired_punctuation_patterns = tuple(
        re.compile(p) for p in data.get("paired_punctuation_patterns", [])
    )

    config = LanguageConfig(
        iso_code=iso_code,
        abbreviations=abbreviations,
        prepositive_abbreviations=prepositive_abbreviations,
        number_abbreviations=number_abbreviations,
        sentence_starters=sentence_starters,
        punctuations=punctuations,
        sentence_boundary_regex=sentence_boundary_regex,
        replace_all_abbr_periods=replace_all_abbr_periods,
        rules=rules,
        clean_rules=clean_rules,
        paired_punctuation_patterns=paired_punctuation_patterns,
        multi_period_abbreviation_regex=multi_period_abbreviation_regex,
    )

    _LANGUAGES_CACHE[code] = config
    return config


def get_language_module(
    lang: str | ModuleType | LanguageConfig | None,
) -> LanguageConfig | None:
    """Return language configuration if lang is non-empty, else None.

    Args:
        lang: Two-letter ISO language code, module, or LanguageConfig.

    Returns:
        The matched LanguageConfig registry object.
    """
    if not lang:
        return None
    if isinstance(lang, LanguageConfig):
        return lang
    if not isinstance(lang, str):
        code = getattr(lang, "ISO_CODE", "")
        if code in SUPPORTED_LANGUAGES:
            return load_language_config(code)
        code = getattr(lang, "iso_code", "")
        if code in SUPPORTED_LANGUAGES:
            return load_language_config(code)
        return None

    return load_language_config(lang)


@dataclass(frozen=True, slots=True)
class Language:
    """Convenience language wrapper for ISO code lookups."""

    code: str

    @classmethod
    def get_language_code(cls, code: str) -> LanguageConfig:
        return load_language_config(code)


def __getattr__(name: str) -> object:
    if name == "LANGUAGE_CODES":
        # Load all configs to populate dictionary for backward compatibility (e.g. tests)
        return {code: load_language_config(code) for code in SUPPORTED_LANGUAGES}
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
