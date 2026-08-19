"""Processing Pipeline Orchestrator for Sentence Boundary Disambiguation."""

from __future__ import annotations

import re
from typing import TYPE_CHECKING

from pragmatic_sbd.abbreviation_replacer import replace_abbreviations
from pragmatic_sbd.lang.common import common, standard
from pragmatic_sbd.lang.common.standard import (
    BETWEEN_SINGLE_QUOTES_REGEX,
    COMMON_RULES,
    DOUBLE_PUNCTUATION_RULES,
    ELLIPSIS_RULES,
    PUA_NEWLINE,
    STANDARD_PAIRED_PATTERNS,
    WORD_WITH_LEADING_APOSTROPHE,
    mask_exclamation_words,
    mask_punctuation,
    mask_single_quote_punctuation,
    unmask_all,
)
from pragmatic_sbd.languages import get_language_module
from pragmatic_sbd.lists_item_replacer import mask_list_items

if TYPE_CHECKING:
    from types import ModuleType

LINE_SPLIT_REGEX = re.compile(rf"(?:\r\n|\r|\n|{PUA_NEWLINE})")


def mask_between_punctuation(text: str, lang: str = "") -> str:
    """Mask punctuation enclosed within paired quotes, brackets, parens, and dashes."""
    if not text:
        return text

    # 1. Single quotes with apostrophe collision check
    if not (WORD_WITH_LEADING_APOSTROPHE.search(text) and not re.search(r"'\s", text)):
        text = BETWEEN_SINGLE_QUOTES_REGEX.sub(mask_single_quote_punctuation, text)

    # 2. Standard paired patterns (double quotes, brackets, parens, em-dashes, etc.)
    for pattern, handler in STANDARD_PAIRED_PATTERNS:
        text = pattern.sub(handler, text)

    # 3. Language-specific paired patterns (e.g., Japanese 「」/（）, Slovak „“, German „“/,,“)
    lang_module = get_language_module(lang) if lang else None
    lang_paired_patterns: tuple[re.Pattern[str], ...] = (
        getattr(lang_module, "PAIRED_PUNCTUATION_PATTERNS", ()) if lang_module else ()
    )
    for custom_pattern in lang_paired_patterns:
        text = custom_pattern.sub(mask_punctuation, text)

    return text


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
        text = mask_list_items(text, lang=self.lang)

        # 2. Abbreviations: Mask periods in honorifics, initials, acronyms
        text = replace_abbreviations(text, lang=self.lang)

        # 3. Numbers & Dates: Mask decimals, versions, timestamps
        text = self._mask_numbers_and_dates(text)

        # 4. Exclamation words: Mask internal exclamation marks (e.g., 'Yahoo!')
        text = mask_exclamation_words(text)

        # 5. Paired punctuation: Mask enclosed periods/punctuation
        text = self._check_for_parens_between_quotes(text)
        text = mask_between_punctuation(text, lang=self.lang)

        # 6. Continuous & Common punctuation
        text = self._mask_continuous_punctuation(text)
        for rule in COMMON_RULES:
            text = rule.pattern.sub(rule.replacement, text)

        # 7. Boundary splitting
        return self._split_into_segments(text)

    def _check_for_parens_between_quotes(self, text: str) -> str:
        """Insert break delimiters around parenthetical citations between double quotes."""

        def _paren_replace(m: re.Match[str]) -> str:
            match = m.group(0)
            sub1 = re.sub(r"\s(?=\()", "\r", match)
            return re.sub(r"(?<=\))\s", "\r", sub1)

        return common.PARENS_BETWEEN_DOUBLE_QUOTES_REGEX.sub(_paren_replace, text)

    def _mask_numbers_and_dates(self, text: str) -> str:
        """Mask periods in decimal numbers, timestamps, and language-specific date formats."""
        for rule in common.NUMBER_RULES:
            text = rule.pattern.sub(rule.replacement, text)

        def _ref_sub(m: re.Match[str]) -> str:
            ref = m.group("ref")
            space = m.group("space") or ""
            if m.end() == len(m.string):
                return f"{standard.PUA_PERIOD}{ref}"
            return f"{standard.PUA_PERIOD}{ref}{space}\r"

        text = common.NUMBERED_REFERENCE_REGEX.sub(_ref_sub, text)

        if self.lang_module:
            for rule in getattr(self.lang_module, "RULES", ()):
                text = rule.pattern.sub(rule.replacement, text)

        return text

    def _mask_continuous_punctuation(self, text: str) -> str:
        """Mask double punctuation marks and multi-dot ellipses."""

        def _cont_repl(m: re.Match[str]) -> str:
            return m.group(1).replace("!", standard.PUA_EXCLAMATION).replace("?", standard.PUA_QUESTION)

        text = common.CONTINUOUS_PUNCTUATION_REGEX.sub(_cont_repl, text)
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

        search_punctuations = punctuations | {
            standard.PUA_PERIOD,
            standard.PUA_EXCLAMATION,
            standard.PUA_QUESTION,
            standard.PUA_DOUBLE_QE,
            standard.PUA_DOUBLE_EQ,
            standard.PUA_DOUBLE_QQ,
            standard.PUA_DOUBLE_EE,
            standard.PUA_TEMP_END_PUNCT,
        }

        quote_regex = (
            getattr(self.lang_module, "QUOTATION_AT_END_OF_SENTENCE_REGEX", None)
            if self.lang_module
            else None
        ) or common.QUOTATION_AT_END_OF_SENTENCE_REGEX

        split_quote_regex = (
            getattr(self.lang_module, "SPLIT_SPACE_QUOTATION_AT_END_OF_SENTENCE_REGEX", None)
            if self.lang_module
            else None
        ) or common.SPLIT_SPACE_QUOTATION_AT_END_OF_SENTENCE_REGEX

        segments: list[str] = []
        for line in LINE_SPLIT_REGEX.split(text):
            if not line:
                continue
            if any(p in line for p in search_punctuations):
                proc_line = line if line[-1] in punctuations else (line + standard.PUA_TEMP_END_PUNCT)
                matches = list(boundary_regex.finditer(proc_line))
                if matches:
                    for m in matches:
                        match_str = m.group(0)
                        if quote_regex.search(match_str):
                            parts = split_quote_regex.split(match_str)
                            segments.extend(unmask_all(p).strip() for p in parts if p.strip())
                        else:
                            cleaned_seg = unmask_all(match_str).strip()
                            if cleaned_seg:
                                segments.append(cleaned_seg)
                else:
                    raw = unmask_all(line).strip()
                    if raw:
                        segments.append(raw)
            else:
                raw = unmask_all(line).strip()
                if raw:
                    segments.append(raw)

        return segments
