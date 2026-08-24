"""Processing Pipeline Orchestrator for Sentence Boundary Disambiguation."""

from __future__ import annotations

import re
from dataclasses import dataclass

from fracture.language.protocols import LanguageProtocol
from fracture.processors import (
    LanguageAbbreviationData,
    apply_replacements,
    get_language_abbreviation_data,
    mask_alphabetical_lists,
    mask_list_items,
    mask_numbered_lists,
    mask_parenthesized_and_roman_lists,
    replace_abbreviation_as_sentence_boundary,
    replace_abbreviations,
    search_for_abbreviations_in_string,
)
from fracture.rules import (
    BETWEEN_DOUBLE_QUOTES_REGEX,
    BETWEEN_EM_DASHES_REGEX,
    BETWEEN_PARENS_REGEX,
    BETWEEN_QUOTE_ARROW_REGEX,
    BETWEEN_QUOTE_SLANTED_REGEX,
    BETWEEN_SINGLE_QUOTE_SLANTED_REGEX,
    BETWEEN_SINGLE_QUOTES_REGEX,
    BETWEEN_SQUARE_BRACKETS_REGEX,
    ELLIPSIS_RULES,
    LINE_SPLIT_REGEX,
    NUMBER_RULES,
    NUMBERED_REFERENCE_REGEX,
    PARENS_BETWEEN_DOUBLE_QUOTES_REGEX,
    PARENS_LEAD_SPACE_REGEX,
    PARENS_TRAIL_SPACE_REGEX,
    PUA_PERIOD,
    PUA_SEARCH_PUNCTUATIONS,
    PUA_TEMP_END_PUNCT,
    PUNCTUATIONS,
    QUOTATION_AT_END_OF_SENTENCE_REGEX,
    SENTENCE_BOUNDARY_REGEX,
    SPLIT_SPACE_QUOTATION_AT_END_OF_SENTENCE_REGEX,
    WORD_WITH_LEADING_APOSTROPHE,
    mask_common_rules,
    mask_exclamation_words,
    mask_punctuation,
    mask_single_quote_punctuation,
    unmask_all,
)

__all__ = [
    "LanguageAbbreviationData",
    "ParagraphChunk",
    "apply_replacements",
    "check_for_parens_between_quotes",
    "disambiguate",
    "get_language_abbreviation_data",
    "mask_alphabetical_lists",
    "mask_between_punctuation",
    "mask_common_rules",
    "mask_continuous_punctuation",
    "mask_exclamation_words",
    "mask_list_items",
    "mask_numbered_lists",
    "mask_numbers_and_dates",
    "mask_parenthesized_and_roman_lists",
    "replace_abbreviation_as_sentence_boundary",
    "replace_abbreviations",
    "search_for_abbreviations_in_string",
    "split_into_segments",
    "trim_span",
]


# =============================================================================
# 1. Paired Punctuation Masking
# =============================================================================


def mask_between_punctuation(text: str, config: LanguageProtocol | None = None) -> str:
    """Mask punctuation enclosed within paired quotes, brackets, parens, and dashes.

    Args:
        text: The input text string.
        config: Optional language configuration.

    Returns:
        The text with punctuation inside quotes or brackets masked.
    """
    if "'" in text and not (
        WORD_WITH_LEADING_APOSTROPHE.search(text) and not re.search(r"'\s", text)
    ):
        text = BETWEEN_SINGLE_QUOTES_REGEX.sub(mask_single_quote_punctuation, text)

    if '"' in text:
        text = BETWEEN_DOUBLE_QUOTES_REGEX.sub(mask_punctuation, text)
    if "\u00ab" in text:
        text = BETWEEN_QUOTE_ARROW_REGEX.sub(mask_punctuation, text)
    if "\u201c" in text:
        text = BETWEEN_QUOTE_SLANTED_REGEX.sub(mask_punctuation, text)
    if "[" in text:
        text = BETWEEN_SQUARE_BRACKETS_REGEX.sub(mask_punctuation, text)
    if "(" in text:
        text = BETWEEN_PARENS_REGEX.sub(mask_punctuation, text)
    if "\u2018" in text:
        text = BETWEEN_SINGLE_QUOTE_SLANTED_REGEX.sub(mask_punctuation, text)
    if "--" in text:
        text = BETWEEN_EM_DASHES_REGEX.sub(mask_punctuation, text)

    lang_module = config
    lang_paired_patterns: tuple[re.Pattern[str], ...] = (
        lang_module.paired_punctuation_patterns if lang_module is not None else ()
    )
    for custom_pattern in lang_paired_patterns:
        text = custom_pattern.sub(mask_punctuation, text)

    return text


# =============================================================================
# 2. Pipeline Orchestrator
# =============================================================================


@dataclass(slots=True, frozen=True)
class ParagraphChunk:
    """Zero-copy index slice representing a single paragraph boundary.

    Attributes:
        start: Starting character offset in the source document.
        end: Ending character offset in the source document.
    """

    start: int
    end: int


def disambiguate(
    text: str,
    *,
    config: LanguageProtocol | None = None,
    char_span: bool = False,
) -> tuple[tuple[int, int], ...] | tuple[str, ...]:
    """Execute the full 1:1 length-preserving disambiguation and extraction pipeline.

    Args:
        text: The source text string to disambiguate.
        config: Optional language-specific configuration protocol.
        char_span: If True, returns a tuple of (start, end) offset integer pairs.
            If False, returns a tuple of sentence strings with all PUA masks restored.

    Returns:
        A tuple of (start, end) offset tuples if char_span is True, else a tuple of sentence strings.
    """
    if not text:
        return ()

    masked_text = text
    has_period = ("." in text) or ("\uff0e" in text) or ("\u3002" in text)
    has_excl = ("!" in text) or ("\uff01" in text)
    has_quest = ("?" in text) or ("\uff1f" in text)
    has_punct = has_period or has_excl or has_quest
    has_custom_rules = config is not None and bool(config.rules)

    # 1. Lists: Mask list numbers and format markers
    if has_period or ")" in text or "•" in text or "⁃" in text:
        masked_text = mask_list_items(masked_text, config=config)

    # 2. Abbreviations: Mask periods in honorifics, initials, acronyms
    if has_period:
        masked_text = replace_abbreviations(masked_text, config=config)

    # 3. Numbers & Dates: Mask decimals, versions, timestamps
    if has_period or has_custom_rules:
        masked_text = mask_numbers_and_dates(masked_text, config=config)

    # 4. Exclamation words: Mask internal exclamation marks (e.g., 'Yahoo!')
    if has_excl:
        masked_text = mask_exclamation_words(masked_text)

    # 5. Paired punctuation: Mask enclosed periods/punctuation
    if has_punct or (config is not None and bool(config.paired_punctuation_patterns)):
        masked_text = check_for_parens_between_quotes(masked_text)
        masked_text = mask_between_punctuation(masked_text, config=config)

    # 6. Continuous & Common punctuation
    if has_punct or "\n" in text:
        masked_text = mask_continuous_punctuation(masked_text)
        masked_text = mask_common_rules(masked_text)

    # 7. Boundary splitting
    spans = split_into_segments(masked_text, config=config)

    if char_span:
        return spans

    return tuple(unmask_all(masked_text[start:end]) for start, end in spans)


def trim_span(text: str, start: int, end: int) -> tuple[int, int] | None:
    """Trim leading and trailing whitespace from a span without string allocation.

    Args:
        text: The source text string.
        start: Starting character offset.
        end: Ending character offset.

    Returns:
        Adjusted (start, end) offsets, or None if the span contains only whitespace.
    """
    while start < end and text[start].isspace():
        start += 1
    while end > start and text[end - 1].isspace():
        end -= 1
    if start < end:
        return (start, end)
    return None


def check_for_parens_between_quotes(text: str) -> str:
    """Insert break delimiters around parenthetical citations between double quotes.

    Args:
        text: The text string to process.

    Returns:
        The text with breaks around parentheticals.
    """

    def _paren_replace(match: re.Match[str]) -> str:
        matched_text = match.group(0)
        leading_space_replaced = PARENS_LEAD_SPACE_REGEX.sub("\r", matched_text)
        return PARENS_TRAIL_SPACE_REGEX.sub("\r", leading_space_replaced)

    return PARENS_BETWEEN_DOUBLE_QUOTES_REGEX.sub(_paren_replace, text)


def mask_numbers_and_dates(text: str, config: LanguageProtocol | None = None) -> str:
    """Mask periods in decimal numbers, timestamps, and date formats.

    Args:
        text: The text string to process.
        config: Optional language configuration.

    Returns:
        The text with number/date periods masked.
    """
    for rule in NUMBER_RULES:
        text = rule.pattern.sub(rule.replacement, text)

    def _ref_sub(match: re.Match[str]) -> str:
        reference = match.group("ref")
        trailing_space = match.group("space") or ""
        if trailing_space:
            # Replace the trailing space char 1:1 with \r delimiter
            return f"{PUA_PERIOD}{reference}" + ("\r" * len(trailing_space))
        return f"{PUA_PERIOD}{reference}"

    text = NUMBERED_REFERENCE_REGEX.sub(_ref_sub, text)

    if config is not None:
        for rule in config.rules:
            text = rule.pattern.sub(rule.replacement, text)

    return text


def mask_continuous_punctuation(text: str) -> str:
    """Mask multi-dot ellipses.

    Args:
        text: The text string to process.

    Returns:
        The text with multi-dot ellipses masked.
    """
    for rule in ELLIPSIS_RULES:
        text = rule.pattern.sub(rule.replacement, text)
    return text


def split_into_segments(
    text: str, config: LanguageProtocol | None = None
) -> tuple[tuple[int, int], ...]:
    """Split disambiguated text into sentence spans using non-destructive line scanning.

    Args:
        text: The fully masked text string.
        config: Optional language configuration protocol.

    Returns:
        A tuple of (start, end) character offset tuples for each sentence span.
    """
    boundary_regex = (
        config.sentence_boundary_regex
        if config and config.sentence_boundary_regex is not None
        else SENTENCE_BOUNDARY_REGEX
    )
    punctuations = (
        config.punctuations
        if config and config.punctuations is not None
        else PUNCTUATIONS
    )

    search_punctuations = punctuations | PUA_SEARCH_PUNCTUATIONS

    quote_regex = QUOTATION_AT_END_OF_SENTENCE_REGEX
    split_quote_regex = SPLIT_SPACE_QUOTATION_AT_END_OF_SENTENCE_REGEX

    spans: list[tuple[int, int]] = []
    text_len = len(text)
    line_start = 0

    def _has_semantic_content(s: int, e: int) -> bool:
        return any(text[i].isalnum() for i in range(s, e))

    def _add_span(s: int, e: int, *, is_line: bool = False) -> None:
        span = trim_span(text, s, e)
        if span is not None:
            if is_line or _has_semantic_content(span[0], span[1]):
                spans.append(span)
            elif spans:
                # Merge trailing intra-line punctuation-only noise into previous sentence span
                spans[-1] = (spans[-1][0], span[1])

    def _process_line_segment(curr_line_start: int, curr_line_end: int) -> None:
        line_len = curr_line_end - curr_line_start
        if line_len <= 0:
            return
        line = text[curr_line_start:curr_line_end]
        if not search_punctuations.isdisjoint(line):
            has_end_punct = line[-1] in punctuations
            processed_line = line if has_end_punct else (line + PUA_TEMP_END_PUNCT)
            has_match = False
            for match in boundary_regex.finditer(processed_line):
                has_match = True
                local_start = min(match.start(), line_len)
                local_end = min(match.end(), line_len)
                if local_start >= local_end:
                    continue
                matched_slice = line[local_start:local_end]
                if quote_regex.search(matched_slice):
                    sub_start = 0
                    for quote_match in split_quote_regex.finditer(matched_slice):
                        sub_end = quote_match.start()
                        _add_span(
                            curr_line_start + local_start + sub_start,
                            curr_line_start + local_start + sub_end,
                        )
                        sub_start = quote_match.end()
                    if sub_start < len(matched_slice):
                        _add_span(
                            curr_line_start + local_start + sub_start,
                            curr_line_start + local_start + len(matched_slice),
                        )
                else:
                    _add_span(
                        curr_line_start + local_start,
                        curr_line_start + local_end,
                    )
            if not has_match:
                _add_span(curr_line_start, curr_line_end, is_line=True)
        else:
            _add_span(curr_line_start, curr_line_end, is_line=True)

    for line_match in LINE_SPLIT_REGEX.finditer(text):
        line_end = line_match.start()
        _process_line_segment(line_start, line_end)
        line_start = line_match.end()

    if line_start < text_len:
        _process_line_segment(line_start, text_len)

    if not spans:
        fallback = trim_span(text, 0, text_len)
        if fallback is not None:
            return (fallback,)

    return tuple(spans)

