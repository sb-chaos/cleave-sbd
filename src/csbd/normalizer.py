"""Stateless text normalizer and cleaner pipeline with coordinate mapping support."""

import re
from collections.abc import Callable, Sequence
from typing import overload

from csbd.language.protocols import LanguageProtocol
from csbd.models import NormalizationResult, OffsetMap
from csbd.rules import (
    CONSECUTIVE_PERIODS,
    CONSECUTIVE_SLASHES,
    DOUBLE_NL,
    DOUBLE_NL_SPACE,
    ESCAPED_CR,
    ESCAPED_NL,
    HTML_ESCAPED_TAG_RULE,
    HTML_TAG_RULE,
    INLINE_FORMATTING,
    NL_BEFORE_BULLET,
    NL_BEFORE_PERIOD,
    NL_IN_SENTENCE,
    NL_IN_WORD,
    NL_TO_CR,
    NO_SPACE_SENTENCE_COMBINED,
    NORMAL_QUOTES,
    PDF_NEW_LINE_MID_SENTENCE,
    PDF_NEW_LINE_MID_SENTENCE_NOSPACE,
    TABLE_OF_CONTENTS,
    TYPO_ESCAPED_CR,
    TYPO_ESCAPED_NL,
    Rule,
    replace_no_space_sentence,
)

__all__ = [
    "NormalizationResult",
    "check_for_no_space_in_between_sentences",
    "clean_consecutive_characters",
    "clean_inline_formatting",
    "clean_quotations",
    "clean_table_of_contents",
    "normalize",
    "normalize_with_map",
    "remove_newline_in_middle_of_sentence",
    "remove_pdf_line_breaks",
    "replace_escaped_newlines",
    "replace_newlines",
    "strip_html",
]


@overload
def _apply_rule_tracked(
    rule: Rule, text: str, in_map: None = None
) -> tuple[str, None]: ...


@overload
def _apply_rule_tracked(
    rule: Rule, text: str, in_map: OffsetMap
) -> tuple[str, OffsetMap]: ...


def _apply_rule_tracked(
    rule: Rule,
    text: str,
    in_map: OffsetMap | None = None,
) -> tuple[str, OffsetMap | None]:
    """Apply a regular expression replacement rule with coordinate delta tracking."""
    if in_map is None:
        return rule.pattern.sub(rule.replacement, text), None

    chunks: list[str] = []
    last_idx = 0
    curr_clean_pos = 0
    clean_keys: list[int] = []
    cum_deltas: list[int] = []

    def record_edit(k: int, d: int) -> None:
        if clean_keys and clean_keys[-1] == k:
            cum_deltas[-1] = d
        elif not cum_deltas or cum_deltas[-1] != d:
            clean_keys.append(k)
            cum_deltas.append(d)

    in_keys_len = len(in_map.clean_keys)
    k_idx = 0
    has_match = False

    for match in rule.pattern.finditer(text):
        has_match = True
        m_start = match.start()
        m_end = match.end()

        # Forward keys from in_map that fall in (last_idx, m_start]
        while k_idx < in_keys_len and in_map.clean_keys[k_idx] <= m_start:
            k = in_map.clean_keys[k_idx]
            shifted_k = curr_clean_pos + (k - last_idx)
            d_shifted = in_map.clean_to_raw(k) - shifted_k
            record_edit(shifted_k, d_shifted)
            k_idx += 1

        unchanged = text[last_idx:m_start]
        chunks.append(unchanged)
        curr_clean_pos += len(unchanged)

        # Compute replacement
        repl = match.expand(rule.replacement)
        chunks.append(repl)
        curr_clean_pos += len(repl)

        # Compute delta to raw at end of repl
        raw_at_end = in_map.clean_to_raw(m_end)
        d_new = raw_at_end - curr_clean_pos
        record_edit(curr_clean_pos, d_new)

        # Advance k_idx past any in_map keys inside replaced range
        while k_idx < in_keys_len and in_map.clean_keys[k_idx] <= m_end:
            k_idx += 1

        last_idx = m_end

    if not has_match:
        return text, in_map

    # Forward remaining in_map keys
    while k_idx < in_keys_len:
        k = in_map.clean_keys[k_idx]
        shifted_k = curr_clean_pos + (k - last_idx)
        d_shifted = in_map.clean_to_raw(k) - shifted_k
        record_edit(shifted_k, d_shifted)
        k_idx += 1

    tail = text[last_idx:]
    chunks.append(tail)
    out_text = "".join(chunks)
    out_map = OffsetMap(
        clean_keys=tuple(clean_keys),
        cum_deltas=tuple(cum_deltas),
        raw_length=in_map.raw_length,
        clean_length=len(out_text),
    )
    return out_text, out_map


@overload
def _apply_sub_fn_tracked(
    pattern: re.Pattern[str],
    repl_fn: Callable[[re.Match[str]], str],
    text: str,
    in_map: None = None,
) -> tuple[str, None]: ...


@overload
def _apply_sub_fn_tracked(
    pattern: re.Pattern[str],
    repl_fn: Callable[[re.Match[str]], str],
    text: str,
    in_map: OffsetMap,
) -> tuple[str, OffsetMap]: ...


def _apply_sub_fn_tracked(
    pattern: re.Pattern[str],
    repl_fn: Callable[[re.Match[str]], str],
    text: str,
    in_map: OffsetMap | None = None,
) -> tuple[str, OffsetMap | None]:
    """Apply a dynamic substitution function with coordinate delta tracking."""
    if in_map is None:
        return pattern.sub(repl_fn, text), None

    chunks: list[str] = []
    last_idx = 0
    curr_clean_pos = 0
    clean_keys: list[int] = []
    cum_deltas: list[int] = []

    def record_edit(k: int, d: int) -> None:
        if clean_keys and clean_keys[-1] == k:
            cum_deltas[-1] = d
        elif not cum_deltas or cum_deltas[-1] != d:
            clean_keys.append(k)
            cum_deltas.append(d)

    in_keys_len = len(in_map.clean_keys)
    k_idx = 0
    has_match = False

    for match in pattern.finditer(text):
        has_match = True
        m_start = match.start()
        m_end = match.end()

        # Forward keys from in_map that fall in (last_idx, m_start]
        while k_idx < in_keys_len and in_map.clean_keys[k_idx] <= m_start:
            k = in_map.clean_keys[k_idx]
            shifted_k = curr_clean_pos + (k - last_idx)
            d_shifted = in_map.clean_to_raw(k) - shifted_k
            record_edit(shifted_k, d_shifted)
            k_idx += 1

        unchanged = text[last_idx:m_start]
        chunks.append(unchanged)
        curr_clean_pos += len(unchanged)

        # Compute replacement
        repl = repl_fn(match)
        chunks.append(repl)
        curr_clean_pos += len(repl)

        # Compute delta to raw at end of repl
        raw_at_end = in_map.clean_to_raw(m_end)
        d_new = raw_at_end - curr_clean_pos
        record_edit(curr_clean_pos, d_new)

        # Advance k_idx past any in_map keys inside replaced range
        while k_idx < in_keys_len and in_map.clean_keys[k_idx] <= m_end:
            k_idx += 1

        last_idx = m_end

    if not has_match:
        return text, in_map

    # Forward remaining in_map keys
    while k_idx < in_keys_len:
        k = in_map.clean_keys[k_idx]
        shifted_k = curr_clean_pos + (k - last_idx)
        d_shifted = in_map.clean_to_raw(k) - shifted_k
        record_edit(shifted_k, d_shifted)
        k_idx += 1

    tail = text[last_idx:]
    chunks.append(tail)
    out_text = "".join(chunks)
    out_map = OffsetMap(
        clean_keys=tuple(clean_keys),
        cum_deltas=tuple(cum_deltas),
        raw_length=in_map.raw_length,
        clean_length=len(out_text),
    )
    return out_text, out_map


@overload
def strip_html(text: str, offset_map: None = None) -> str: ...


@overload
def strip_html(text: str, offset_map: OffsetMap) -> tuple[str, OffsetMap]: ...


def strip_html(
    text: str, offset_map: OffsetMap | None = None
) -> tuple[str, OffsetMap] | str:
    """Strip HTML tags and escaped HTML entities."""
    if offset_map is None:
        if "<" in text:
            text = HTML_TAG_RULE.pattern.sub(HTML_TAG_RULE.replacement, text)
        if "&lt;" in text:
            text = HTML_ESCAPED_TAG_RULE.pattern.sub(
                HTML_ESCAPED_TAG_RULE.replacement, text
            )
        return text

    if "<" in text:
        text, offset_map = _apply_rule_tracked(HTML_TAG_RULE, text, offset_map)
    if "&lt;" in text:
        text, offset_map = _apply_rule_tracked(HTML_ESCAPED_TAG_RULE, text, offset_map)
    return text, offset_map


@overload
def clean_inline_formatting(text: str, offset_map: None = None) -> str: ...


@overload
def clean_inline_formatting(
    text: str, offset_map: OffsetMap
) -> tuple[str, OffsetMap]: ...


def clean_inline_formatting(
    text: str, offset_map: OffsetMap | None = None
) -> tuple[str, OffsetMap] | str:
    """Remove inline formatting tags (e.g. {b^>1<b^})."""
    if "{b^" in text:
        if offset_map is None:
            return INLINE_FORMATTING.pattern.sub(INLINE_FORMATTING.replacement, text)
        return _apply_rule_tracked(INLINE_FORMATTING, text, offset_map)
    return (text, offset_map) if offset_map is not None else text


@overload
def clean_quotations(text: str, offset_map: None = None) -> str: ...


@overload
def clean_quotations(text: str, offset_map: OffsetMap) -> tuple[str, OffsetMap]: ...


def clean_quotations(
    text: str, offset_map: OffsetMap | None = None
) -> tuple[str, OffsetMap] | str:
    """Normalize backticks and duplicated quote characters."""
    if offset_map is None:
        if "`" in text or "''" in text:
            if "`" in text:
                text = text.replace("`", "'")
            if "''" in text:
                text = NORMAL_QUOTES.pattern.sub(NORMAL_QUOTES.replacement, text)
        return text

    if "`" in text or "''" in text:
        if "`" in text:
            text = text.replace("`", "'")
        if "''" in text:
            text, offset_map = _apply_rule_tracked(NORMAL_QUOTES, text, offset_map)
    return text, offset_map


@overload
def clean_table_of_contents(text: str, offset_map: None = None) -> str: ...


@overload
def clean_table_of_contents(
    text: str, offset_map: OffsetMap
) -> tuple[str, OffsetMap]: ...


def clean_table_of_contents(
    text: str, offset_map: OffsetMap | None = None
) -> tuple[str, OffsetMap] | str:
    """Clean leader dots in table-of-contents entries."""
    if "...." in text:
        if offset_map is None:
            return TABLE_OF_CONTENTS.pattern.sub(TABLE_OF_CONTENTS.replacement, text)
        return _apply_rule_tracked(TABLE_OF_CONTENTS, text, offset_map)
    return (text, offset_map) if offset_map is not None else text


@overload
def clean_consecutive_characters(text: str, offset_map: None = None) -> str: ...


@overload
def clean_consecutive_characters(
    text: str, offset_map: OffsetMap
) -> tuple[str, OffsetMap]: ...


def clean_consecutive_characters(
    text: str, offset_map: OffsetMap | None = None
) -> tuple[str, OffsetMap] | str:
    """Normalize consecutive periods and slashes."""
    if offset_map is None:
        if "....." in text:
            text = CONSECUTIVE_PERIODS.pattern.sub(
                CONSECUTIVE_PERIODS.replacement, text
            )
        if "///" in text:
            text = CONSECUTIVE_SLASHES.pattern.sub(
                CONSECUTIVE_SLASHES.replacement, text
            )
        return text

    if "....." in text:
        text, offset_map = _apply_rule_tracked(CONSECUTIVE_PERIODS, text, offset_map)
    if "///" in text:
        text, offset_map = _apply_rule_tracked(CONSECUTIVE_SLASHES, text, offset_map)
    return text, offset_map


@overload
def check_for_no_space_in_between_sentences(
    text: str, offset_map: None = None
) -> str: ...


@overload
def check_for_no_space_in_between_sentences(
    text: str, offset_map: OffsetMap
) -> tuple[str, OffsetMap]: ...


def check_for_no_space_in_between_sentences(
    text: str, offset_map: OffsetMap | None = None
) -> tuple[str, OffsetMap] | str:
    """Insert spaces in punctuation-joined sentences while protecting URLs/emails."""
    if "." not in text:
        return (text, offset_map) if offset_map is not None else text
    if offset_map is None:
        return NO_SPACE_SENTENCE_COMBINED.sub(replace_no_space_sentence, text)
    return _apply_sub_fn_tracked(
        NO_SPACE_SENTENCE_COMBINED, replace_no_space_sentence, text, offset_map
    )


@overload
def remove_newline_in_middle_of_sentence(text: str, offset_map: None = None) -> str: ...


@overload
def remove_newline_in_middle_of_sentence(
    text: str, offset_map: OffsetMap
) -> tuple[str, OffsetMap]: ...


def remove_newline_in_middle_of_sentence(
    text: str, offset_map: OffsetMap | None = None
) -> tuple[str, OffsetMap] | str:
    """Remove mid-sentence line breaks within words and clauses."""
    if offset_map is None:
        text = NL_IN_WORD.pattern.sub(NL_IN_WORD.replacement, text)
        return NL_IN_SENTENCE.pattern.sub(NL_IN_SENTENCE.replacement, text)
    text, offset_map = _apply_rule_tracked(NL_IN_WORD, text, offset_map)
    text, offset_map = _apply_rule_tracked(NL_IN_SENTENCE, text, offset_map)
    return text, offset_map


@overload
def remove_pdf_line_breaks(text: str, offset_map: None = None) -> str: ...


@overload
def remove_pdf_line_breaks(
    text: str, offset_map: OffsetMap
) -> tuple[str, OffsetMap]: ...


def remove_pdf_line_breaks(
    text: str, offset_map: OffsetMap | None = None
) -> tuple[str, OffsetMap] | str:
    """Handle PDF-specific line-wrap breaks and bullet points."""
    if "\n" not in text:
        return (text, offset_map) if offset_map is not None else text
    if offset_map is None:
        text = NL_BEFORE_BULLET.pattern.sub(NL_BEFORE_BULLET.replacement, text)
        text = PDF_NEW_LINE_MID_SENTENCE.pattern.sub(
            PDF_NEW_LINE_MID_SENTENCE.replacement, text
        )
        return PDF_NEW_LINE_MID_SENTENCE_NOSPACE.pattern.sub(
            PDF_NEW_LINE_MID_SENTENCE_NOSPACE.replacement, text
        )
    text, offset_map = _apply_rule_tracked(NL_BEFORE_BULLET, text, offset_map)
    text, offset_map = _apply_rule_tracked(PDF_NEW_LINE_MID_SENTENCE, text, offset_map)
    text, offset_map = _apply_rule_tracked(
        PDF_NEW_LINE_MID_SENTENCE_NOSPACE, text, offset_map
    )
    return text, offset_map


@overload
def replace_newlines(text: str, doc_type: str = "", offset_map: None = None) -> str: ...


@overload
def replace_newlines(
    text: str, doc_type: str, offset_map: OffsetMap
) -> tuple[str, OffsetMap]: ...


@overload
def replace_newlines(text: str, *, offset_map: OffsetMap) -> tuple[str, OffsetMap]: ...


def replace_newlines(
    text: str, doc_type: str = "", offset_map: OffsetMap | None = None
) -> tuple[str, OffsetMap] | str:
    """Normalize newlines based on document type (standard or PDF)."""
    if "\n" not in text:
        return (text, offset_map) if offset_map is not None else text

    if doc_type == "pdf":
        if offset_map is None:
            return remove_pdf_line_breaks(text)
        return remove_pdf_line_breaks(text, offset_map)

    if offset_map is None:
        text = remove_newline_in_middle_of_sentence(text)
        text = DOUBLE_NL_SPACE.pattern.sub(DOUBLE_NL_SPACE.replacement, text)
        text = DOUBLE_NL.pattern.sub(DOUBLE_NL.replacement, text)
        text = NL_BEFORE_PERIOD.pattern.sub(NL_BEFORE_PERIOD.replacement, text)
        return NL_TO_CR.pattern.sub(NL_TO_CR.replacement, text)

    text, offset_map = remove_newline_in_middle_of_sentence(text, offset_map)
    text, offset_map = _apply_rule_tracked(DOUBLE_NL_SPACE, text, offset_map)
    text, offset_map = _apply_rule_tracked(DOUBLE_NL, text, offset_map)
    text, offset_map = _apply_rule_tracked(NL_BEFORE_PERIOD, text, offset_map)
    text, offset_map = _apply_rule_tracked(NL_TO_CR, text, offset_map)
    return text, offset_map


@overload
def replace_escaped_newlines(text: str, offset_map: None = None) -> str: ...


@overload
def replace_escaped_newlines(
    text: str, offset_map: OffsetMap
) -> tuple[str, OffsetMap]: ...


def replace_escaped_newlines(
    text: str, offset_map: OffsetMap | None = None
) -> tuple[str, OffsetMap] | str:
    """Normalize escaped newline and carriage-return strings."""
    if "\\" not in text:
        return (text, offset_map) if offset_map is not None else text

    if offset_map is None:
        text = ESCAPED_NL.pattern.sub(ESCAPED_NL.replacement, text)
        text = ESCAPED_CR.pattern.sub(ESCAPED_CR.replacement, text)
        text = TYPO_ESCAPED_NL.pattern.sub(TYPO_ESCAPED_NL.replacement, text)
        return TYPO_ESCAPED_CR.pattern.sub(TYPO_ESCAPED_CR.replacement, text)

    text, offset_map = _apply_rule_tracked(ESCAPED_NL, text, offset_map)
    text, offset_map = _apply_rule_tracked(ESCAPED_CR, text, offset_map)
    text, offset_map = _apply_rule_tracked(TYPO_ESCAPED_NL, text, offset_map)
    text, offset_map = _apply_rule_tracked(TYPO_ESCAPED_CR, text, offset_map)
    return text, offset_map


def normalize_with_map(
    text: str,
    *,
    config: LanguageProtocol | None = None,
    doc_type: str = "",
    custom_rules: Sequence[Rule] = (),
) -> NormalizationResult:
    """Normalize text while building an OffsetMap for exact coordinate projection back to source text.

    Args:
        text: The source text string.
        config: Optional language configuration module.
        doc_type: Document format override (e.g. 'pdf').
        custom_rules: Custom cleaning rules to apply.

    Returns:
        NormalizationResult containing cleaned text and its coordinate OffsetMap.
    """
    if not text:
        return NormalizationResult(text="", offset_map=OffsetMap.identity(len(text)))

    offset_map: OffsetMap = OffsetMap.identity(len(text))
    cleaned: str = text

    cleaned, offset_map = strip_html(cleaned, offset_map)
    cleaned, offset_map = clean_inline_formatting(cleaned, offset_map)
    cleaned, offset_map = clean_quotations(cleaned, offset_map)
    cleaned, offset_map = clean_table_of_contents(cleaned, offset_map)
    cleaned, offset_map = clean_consecutive_characters(cleaned, offset_map)
    cleaned, offset_map = check_for_no_space_in_between_sentences(cleaned, offset_map)

    rules: tuple[Rule, ...] = tuple(custom_rules)
    if config is not None and config.clean_rules:
        rules = rules + config.clean_rules

    for rule in rules:
        cleaned, offset_map = _apply_rule_tracked(rule, cleaned, offset_map)
        assert offset_map is not None

    cleaned, offset_map = replace_newlines(
        cleaned, doc_type=doc_type, offset_map=offset_map
    )
    cleaned, offset_map = replace_escaped_newlines(cleaned, offset_map=offset_map)

    return NormalizationResult(
        text=cleaned,
        offset_map=offset_map,
    )


def normalize(
    text: str | None,
    *,
    config: LanguageProtocol | None = None,
    doc_type: str = "",
    char_span: bool = False,
    custom_rules: Sequence[Rule] = (),
) -> str | None:
    """Run the complete normalization and cleaning pipeline on input text.

    Args:
        text: The text to normalize.
        config: A language configuration module implementing LanguageProtocol. Defaults to None.
        doc_type: Document format, e.g. "pdf". Defaults to "".
        char_span: Deprecated/legacy parameter. Normalization is now fully offset-mappable.
        custom_rules: Custom cleaning rules to apply. Defaults to ().

    Returns:
        The fully cleaned and normalized string, or None if input was None.
    """
    if text is None:
        return None
    if not text:
        return ""

    result = normalize_with_map(
        text, config=config, doc_type=doc_type, custom_rules=custom_rules
    )
    return result.text
