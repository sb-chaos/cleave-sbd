"""Stateless text normalizer and cleaner pipeline with coordinate mapping support."""

import re
from collections.abc import Callable, Sequence
from dataclasses import dataclass, field

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


@dataclass(slots=True)
class _DeltaCollector:
    """Internal helper to record text replacements and build an OffsetMap."""

    raw_length: int
    clean_keys: list[int] = field(default_factory=list)
    cum_deltas: list[int] = field(default_factory=list)
    running_delta: int = 0

    def record_edit(self, clean_pos: int, raw_delta: int) -> None:
        """Record a single edit step delta.

        Args:
            clean_pos: Character offset in the new cleaned buffer where replacement occurred.
            raw_delta: Net change in length (raw_len - new_len). Positive means raw was longer.
        """
        self.running_delta += raw_delta
        if self.clean_keys and self.clean_keys[-1] == clean_pos:
            self.cum_deltas[-1] = self.running_delta
        else:
            self.clean_keys.append(clean_pos)
            self.cum_deltas.append(self.running_delta)

    def build_map(self, clean_length: int) -> OffsetMap:
        """Build the immutable OffsetMap."""
        return OffsetMap(
            clean_keys=tuple(self.clean_keys),
            cum_deltas=tuple(self.cum_deltas),
            raw_length=self.raw_length,
            clean_length=clean_length,
        )


def _apply_rule_tracked(
    rule: Rule, text: str, collector: _DeltaCollector | None = None
) -> str:
    """Apply a regular expression replacement rule with optional delta tracking."""
    if collector is None:
        return rule.pattern.sub(rule.replacement, text)

    chunks: list[str] = []
    last_idx = 0
    curr_clean_pos = 0

    for match in rule.pattern.finditer(text):
        m_start = match.start()
        m_end = match.end()

        # Append preceding unchanged slice
        unchanged = text[last_idx:m_start]
        chunks.append(unchanged)
        curr_clean_pos += len(unchanged)

        # Compute replacement
        repl = match.expand(rule.replacement)
        chunks.append(repl)

        # Delta calculation: (orig_matched_chars - replaced_chars)
        raw_diff = (m_end - m_start) - len(repl)
        curr_clean_pos += len(repl)
        if raw_diff != 0:
            collector.record_edit(curr_clean_pos, raw_diff)

        last_idx = m_end

    tail = text[last_idx:]
    chunks.append(tail)
    return "".join(chunks)


def _apply_sub_fn_tracked(
    pattern: re.Pattern[str],
    repl_fn: Callable[[re.Match[str]], str],
    text: str,
    collector: _DeltaCollector | None = None,
) -> str:
    """Apply a dynamic substitution function with optional delta tracking."""
    if collector is None:
        return pattern.sub(repl_fn, text)

    chunks: list[str] = []
    last_idx = 0
    curr_clean_pos = 0

    for match in pattern.finditer(text):
        m_start = match.start()
        m_end = match.end()

        unchanged = text[last_idx:m_start]
        chunks.append(unchanged)
        curr_clean_pos += len(unchanged)

        repl = repl_fn(match)
        chunks.append(repl)

        raw_diff = (m_end - m_start) - len(repl)
        curr_clean_pos += len(repl)
        if raw_diff != 0:
            collector.record_edit(curr_clean_pos, raw_diff)

        last_idx = m_end

    tail = text[last_idx:]
    chunks.append(tail)
    return "".join(chunks)


def strip_html(text: str, collector: _DeltaCollector | None = None) -> str:
    """Strip HTML tags and escaped HTML entities."""
    if "<" in text:
        text = _apply_rule_tracked(HTML_TAG_RULE, text, collector)
    if "&lt;" in text:
        text = _apply_rule_tracked(HTML_ESCAPED_TAG_RULE, text, collector)
    return text


def clean_inline_formatting(text: str, collector: _DeltaCollector | None = None) -> str:
    """Remove inline formatting tags (e.g. {b^>1<b^})."""
    if "{b^" in text:
        return _apply_rule_tracked(INLINE_FORMATTING, text, collector)
    return text


def clean_quotations(text: str, collector: _DeltaCollector | None = None) -> str:
    """Normalize backticks and duplicated quote characters."""
    if "`" in text or "''" in text:
        if "`" in text:
            # 1:1 replacement doesn't shift length, but tracked safe
            text = text.replace("`", "'")
        if "''" in text:
            text = _apply_rule_tracked(NORMAL_QUOTES, text, collector)
    return text


def clean_table_of_contents(text: str, collector: _DeltaCollector | None = None) -> str:
    """Clean leader dots in table-of-contents entries."""
    if "...." in text:
        return _apply_rule_tracked(TABLE_OF_CONTENTS, text, collector)
    return text


def clean_consecutive_characters(
    text: str, collector: _DeltaCollector | None = None
) -> str:
    """Normalize consecutive periods and slashes."""
    if "....." in text:
        text = _apply_rule_tracked(CONSECUTIVE_PERIODS, text, collector)
    if "///" in text:
        text = _apply_rule_tracked(CONSECUTIVE_SLASHES, text, collector)
    return text


def check_for_no_space_in_between_sentences(
    text: str, collector: _DeltaCollector | None = None
) -> str:
    """Insert spaces in punctuation-joined sentences while protecting URLs/emails."""
    if "." not in text:
        return text
    return _apply_sub_fn_tracked(
        NO_SPACE_SENTENCE_COMBINED, replace_no_space_sentence, text, collector
    )


def remove_newline_in_middle_of_sentence(
    text: str, collector: _DeltaCollector | None = None
) -> str:
    """Remove mid-sentence line breaks within words and clauses."""
    text = _apply_rule_tracked(NL_IN_WORD, text, collector)
    return _apply_rule_tracked(NL_IN_SENTENCE, text, collector)


def remove_pdf_line_breaks(text: str, collector: _DeltaCollector | None = None) -> str:
    """Handle PDF-specific line-wrap breaks and bullet points."""
    if "\n" not in text:
        return text
    text = _apply_rule_tracked(NL_BEFORE_BULLET, text, collector)
    text = _apply_rule_tracked(PDF_NEW_LINE_MID_SENTENCE, text, collector)
    return _apply_rule_tracked(PDF_NEW_LINE_MID_SENTENCE_NOSPACE, text, collector)


def replace_newlines(
    text: str, doc_type: str = "", collector: _DeltaCollector | None = None
) -> str:
    """Normalize newlines based on document type (standard or PDF)."""
    if "\n" not in text:
        return text

    if doc_type == "pdf":
        return remove_pdf_line_breaks(text, collector)

    text = remove_newline_in_middle_of_sentence(text, collector)
    text = _apply_rule_tracked(DOUBLE_NL_SPACE, text, collector)
    text = _apply_rule_tracked(DOUBLE_NL, text, collector)
    text = _apply_rule_tracked(NL_BEFORE_PERIOD, text, collector)
    return _apply_rule_tracked(NL_TO_CR, text, collector)


def replace_escaped_newlines(
    text: str, collector: _DeltaCollector | None = None
) -> str:
    """Normalize escaped newline and carriage-return strings."""
    if "\\" not in text:
        return text
    text = _apply_rule_tracked(ESCAPED_NL, text, collector)
    text = _apply_rule_tracked(ESCAPED_CR, text, collector)
    text = _apply_rule_tracked(TYPO_ESCAPED_NL, text, collector)
    return _apply_rule_tracked(TYPO_ESCAPED_CR, text, collector)


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

    collector = _DeltaCollector(raw_length=len(text))

    cleaned = strip_html(text, collector)
    cleaned = clean_inline_formatting(cleaned, collector)
    cleaned = clean_quotations(cleaned, collector)
    cleaned = clean_table_of_contents(cleaned, collector)
    cleaned = clean_consecutive_characters(cleaned, collector)
    cleaned = check_for_no_space_in_between_sentences(cleaned, collector)

    rules: tuple[Rule, ...] = tuple(custom_rules)
    if config is not None and config.clean_rules:
        rules = rules + config.clean_rules

    for rule in rules:
        cleaned = _apply_rule_tracked(rule, cleaned, collector)

    cleaned = replace_newlines(cleaned, doc_type=doc_type, collector=collector)
    cleaned = replace_escaped_newlines(cleaned, collector=collector)

    return NormalizationResult(
        text=cleaned,
        offset_map=collector.build_map(clean_length=len(cleaned)),
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
