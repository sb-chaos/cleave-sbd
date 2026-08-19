"""Backward compatibility wrapper for Disambiguator (formerly Processor)."""

from pragmatic_sbd.disambiguator import (
    AbbreviationReplacer,
    Disambiguator,
    LanguageAbbreviationData,
    ListItemReplacer,
    Processor,
    get_language_abbreviation_data,
    mask_between_punctuation,
    mask_exclamation_words,
    mask_list_items,
    replace_abbreviation_as_sentence_boundary,
    replace_abbreviations,
    replace_multi_period_abbreviations,
    replace_period_of_abbr,
    replace_pre_number_abbr,
    replace_prepositive_abbr,
    search_for_abbreviations_in_string,
)

__all__ = [
    "AbbreviationReplacer",
    "Disambiguator",
    "LanguageAbbreviationData",
    "ListItemReplacer",
    "Processor",
    "get_language_abbreviation_data",
    "mask_between_punctuation",
    "mask_exclamation_words",
    "mask_list_items",
    "replace_abbreviation_as_sentence_boundary",
    "replace_abbreviations",
    "replace_multi_period_abbreviations",
    "replace_period_of_abbr",
    "replace_pre_number_abbr",
    "replace_prepositive_abbr",
    "search_for_abbreviations_in_string",
]
