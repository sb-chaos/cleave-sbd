from functools import lru_cache
from types import ModuleType

from pragmatic_sbd.lang import (
    amharic,
    arabic,
    armenian,
    bulgarian,
    burmese,
    chinese,
    danish,
    deutsch,
    dutch,
    english,
    french,
    greek,
    hindi,
    italian,
    japanese,
    kazakh,
    marathi,
    persian,
    polish,
    russian,
    slovak,
    spanish,
    urdu,
)

LANGUAGE_CODES: dict[str, ModuleType] = {
    "en": english,
    "hi": hindi,
    "mr": marathi,
    "zh": chinese,
    "es": spanish,
    "am": amharic,
    "ar": arabic,
    "hy": armenian,
    "bg": bulgarian,
    "ur": urdu,
    "ru": russian,
    "pl": polish,
    "fa": persian,
    "nl": dutch,
    "da": danish,
    "fr": french,
    "my": burmese,
    "el": greek,
    "it": italian,
    "ja": japanese,
    "de": deutsch,
    "kk": kazakh,
    "sk": slovak,
}


@lru_cache(maxsize=32)
def get_language_module(lang: str) -> ModuleType | None:
    """Return cached language configuration module if lang is non-empty, else None."""
    if not lang:
        return None
    try:
        return LANGUAGE_CODES[lang]
    except KeyError as err:
        raise ValueError(
            f"Provide valid language ID i.e. ISO code. Available codes are : {set(LANGUAGE_CODES.keys())}"
        ) from err


class Language:
    def __init__(self, code: str) -> None:
        self.code = code

    @classmethod
    def get_language_code(cls, code: str) -> ModuleType:
        try:
            return LANGUAGE_CODES[code]
        except KeyError as err:
            raise ValueError(
                f"Provide valid language ID i.e. ISO code. Available codes are : {set(LANGUAGE_CODES.keys())}"
            ) from err
