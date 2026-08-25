"""Language configuration and dynamic loader for Pragmatic SBD."""

from __future__ import annotations

import importlib.resources
import re
import tomllib
from dataclasses import dataclass
from typing import Any

from csbd.rules import Rule

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

__all__ = [
    "SUPPORTED_LANGUAGES",
    "Language",
    "LanguageConfig",
    "get_language_module",
    "load_language_config",
]


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
    ref = importlib.resources.files("csbd.language.configs").joinpath(f"{code}.toml")
    data: dict[str, Any] = tomllib.loads(ref.read_text(encoding="utf-8"))

    # Instantiate the configuration container
    iso_code: str = str(data["iso_code"])
    raw_abbr: list[Any] = data.get("abbreviations", [])
    abbreviations: frozenset[str] = frozenset(str(x) for x in raw_abbr)

    raw_prep: list[Any] = data.get("prepositive_abbreviations", [])
    prepositive_abbreviations: frozenset[str] = frozenset(str(x) for x in raw_prep)

    raw_num_abbr: list[Any] = data.get("number_abbreviations", [])
    number_abbreviations: frozenset[str] = frozenset(str(x) for x in raw_num_abbr)

    raw_starters: list[Any] = data.get("sentence_starters", [])
    sentence_starters: frozenset[str] = frozenset(str(x) for x in raw_starters)

    punctuations: frozenset[str] | None = (
        frozenset(str(x) for x in data["punctuations"])
        if "punctuations" in data
        else None
    )
    replace_all_abbr_periods: bool = bool(data.get("replace_all_abbr_periods", False))

    sentence_boundary_regex: re.Pattern[str] | None = (
        re.compile(str(data["sentence_boundary_regex"]))
        if "sentence_boundary_regex" in data
        else None
    )

    multi_period_abbreviation_regex: re.Pattern[str] | None = (
        re.compile(str(data["multi_period_abbreviation_regex"]))
        if "multi_period_abbreviation_regex" in data
        else None
    )

    raw_rules: list[Any] = data.get("rules", [])
    rules: tuple[Rule, ...] = tuple(
        Rule(
            re.compile(str(r["pattern"])),
            str(r.get("replacement", "")),
        )
        for r in raw_rules
    )

    raw_clean_rules: list[Any] = data.get("clean_rules", [])
    clean_rules: tuple[Rule, ...] = tuple(
        Rule(
            re.compile(str(r["pattern"])),
            str(r.get("replacement", "")),
        )
        for r in raw_clean_rules
    )

    raw_paired: list[Any] = data.get("paired_punctuation_patterns", [])
    paired_punctuation_patterns: tuple[re.Pattern[str], ...] = tuple(
        re.compile(str(p)) for p in raw_paired
    )

    config: LanguageConfig = LanguageConfig(
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
    lang: str | LanguageConfig | None,
) -> LanguageConfig | None:
    """Return language configuration if lang is non-empty, else None.

    Args:
        lang: Two-letter ISO language code or LanguageConfig.

    Returns:
        The matched LanguageConfig registry object.
    """
    if not lang:
        return None
    if isinstance(lang, LanguageConfig):
        return lang
    return load_language_config(lang)


@dataclass(frozen=True, slots=True)
class Language:
    """Convenience language wrapper for ISO code lookups."""

    code: str

    @classmethod
    def get_language_code(cls, code: str) -> LanguageConfig:
        """Lookup and return the language configuration for the given ISO code.

        Args:
            code: Two-letter ISO 639-1 language code.

        Returns:
            The loaded LanguageConfig instance.
        """
        return load_language_config(code)
