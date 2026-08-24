"""Language package entrypoint."""

from csbd.language.lang import (
    SUPPORTED_LANGUAGES,
    Language,
    LanguageConfig,
    get_language_module,
    load_language_config,
)

__all__: list[str] = [
    "SUPPORTED_LANGUAGES",
    "Language",
    "LanguageConfig",
    "get_language_module",
    "load_language_config",
]
