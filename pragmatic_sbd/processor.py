"""Processing Pipeline Orchestrator for Sentence Boundary Disambiguation."""

from __future__ import annotations

import re
from typing import TYPE_CHECKING

from pragmatic_sbd.abbreviation_replacer import replace_abbreviations
from pragmatic_sbd.between_punctuation import mask_between_punctuation
from pragmatic_sbd.exclamation_words import mask_exclamation_words
from pragmatic_sbd.lang.common import common, standard
from pragmatic_sbd.lang.common.standard import (
    COMMON_RULES,
    DOUBLE_PUNCTUATION_RULES,
    ELLIPSIS_RULES,
    PUA_NEWLINE,
    unmask_all,
)
from pragmatic_sbd.languages import get_language_module
from pragmatic_sbd.lists_item_replacer import mask_list_items

if TYPE_CHECKING:
    from types import ModuleType

LINE_SPLIT_REGEX = re.compile(rf"(?:\r\n|\r|\n|{PUA_NEWLINE})")


class Processor:
    """Orchestrates sentence boundary disambiguation and segmentation."""

    def __init__(self, text: str = "", lang: str = "", char_span: bool = False) -> None:
        self.text: str = text or ""
        self.lang: str = lang
        self.char_span: bool = char_span
        self.lang_module: ModuleType | None = get_language_module(lang) if lang else None

    def process(self) -> list[str]:
        """Execute the full 1:1 length-preserving disambiguation and extraction pipeline."""
        if not self.text:
            return []

        text = self.text

        # 1. Lists: Mask list numbers and format markers
        text = mask_list_items(text)

        # 2. Abbreviations: Mask periods in honorifics, initials, acronyms
        text = replace_abbreviations(text, lang=self.lang)

        # 3. Numbers & Dates: Mask decimals, versions, timestamps
        text = self._mask_numbers_and_dates(text)

        # 4. Exclamation words: Mask internal exclamation marks (e.g., 'Yahoo!')
        text = mask_exclamation_words(text)

        # 5. Paired punctuation: Mask enclosed periods/punctuation
        text = mask_between_punctuation(text, lang=self.lang)

        # 6. Continuous & Common punctuation
        text = self._mask_continuous_punctuation(text)
        for rule in COMMON_RULES:
            text = rule.pattern.sub(rule.replacement, text)

        # 7. Boundary splitting
        return self._split_into_segments(text)

    def _mask_numbers_and_dates(self, text: str) -> str:
        """Mask periods in decimal numbers, timestamps, and language-specific date formats."""
        for rule in common.NUMBER_RULES:
            text = rule.pattern.sub(rule.replacement, text)

        if self.lang_module:
            for rule in getattr(self.lang_module, "RULES", ()):
                text = rule.pattern.sub(rule.replacement, text)

        return text

    def _mask_continuous_punctuation(self, text: str) -> str:
        """Mask double punctuation marks and multi-dot ellipses."""
        for rule in DOUBLE_PUNCTUATION_RULES:
            text = rule.pattern.sub(rule.replacement, text)
        for rule in ELLIPSIS_RULES:
            text = rule.pattern.sub(rule.replacement, text)
        return text

    def _split_into_segments(self, text: str) -> list[str]:
        """Split disambiguated text into sentence segments using boundary regex."""
        boundary_regex = (
            getattr(self.lang_module, "SENTENCE_BOUNDARY_REGEX", None) if self.lang_module else None
        ) or common.SENTENCE_BOUNDARY_REGEX

        punctuations = (
            getattr(self.lang_module, "PUNCTUATIONS", None) if self.lang_module else None
        ) or standard.PUNCTUATIONS

        segments: list[str] = []
        for line in LINE_SPLIT_REGEX.split(text):
            if not line:
                continue
            if any(p in line for p in punctuations):
                matches = list(boundary_regex.finditer(line))
                if matches:
                    segments.extend(m.group(0) for m in matches)
                    last_end = matches[-1].end()
                    if last_end < len(line):
                        trailing = line[last_end:].lstrip()
                        if trailing.strip():
                            segments.append(trailing)
                else:
                    segments.append(line)
            else:
                segments.append(line)

        return [unmask_all(s) for s in segments if s.strip()]
