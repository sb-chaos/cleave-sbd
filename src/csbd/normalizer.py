"""Stateless text normalizer and cleaner pipeline."""

from collections.abc import Sequence

from csbd.language.protocols import LanguageProtocol
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


def strip_html(text: str) -> str:
    """Strip HTML tags and escaped HTML entities.

    Args:
        text: The text string to clean.

    Returns:
        The text with HTML elements removed.
    """
    if "<" in text:
        text = HTML_TAG_RULE.pattern.sub(HTML_TAG_RULE.replacement, text)
    if "&lt;" in text:
        text = HTML_ESCAPED_TAG_RULE.pattern.sub(
            HTML_ESCAPED_TAG_RULE.replacement, text
        )
    return text


def clean_inline_formatting(text: str) -> str:
    """Remove inline formatting tags (e.g. {b^>1<b^}).

    Args:
        text: The text string to clean.

    Returns:
        The text with inline formatting markers removed.
    """
    if "{b^" in text:
        return INLINE_FORMATTING.pattern.sub(INLINE_FORMATTING.replacement, text)
    return text


def clean_quotations(text: str) -> str:
    """Normalize backticks and duplicated quote characters.

    Args:
        text: The text string to clean.

    Returns:
        The text with normalized double and single quotes.
    """
    if "`" in text or "''" in text:
        text = text.replace("`", "'")
        if "''" in text:
            text = NORMAL_QUOTES.pattern.sub(NORMAL_QUOTES.replacement, text)
    return text


def clean_table_of_contents(text: str) -> str:
    """Clean leader dots in table-of-contents entries.

    Args:
        text: The text string to clean.

    Returns:
        The text with table-of-contents line dots cleaned.
    """
    if "...." in text:
        return TABLE_OF_CONTENTS.pattern.sub(TABLE_OF_CONTENTS.replacement, text)
    return text


def clean_consecutive_characters(text: str) -> str:
    """Normalize consecutive periods and slashes.

    Args:
        text: The text string to clean.

    Returns:
        The text with simplified sequences of periods and slashes.
    """
    if "....." in text:
        text = CONSECUTIVE_PERIODS.pattern.sub(CONSECUTIVE_PERIODS.replacement, text)
    if "///" in text:
        text = CONSECUTIVE_SLASHES.pattern.sub(CONSECUTIVE_SLASHES.replacement, text)
    return text


def check_for_no_space_in_between_sentences(text: str) -> str:
    """Insert spaces in punctuation-joined sentences while protecting URLs/emails.

    Args:
        text: The text string to clean.

    Returns:
        The text with spaces inserted after punctuation marks where required.
    """
    if "." not in text:
        return text
    return NO_SPACE_SENTENCE_COMBINED.sub(replace_no_space_sentence, text)


def remove_newline_in_middle_of_sentence(text: str) -> str:
    """Remove mid-sentence line breaks within words and clauses.

    Args:
        text: The text string to clean.

    Returns:
        The text with mid-sentence line breaks removed.
    """
    text = NL_IN_WORD.pattern.sub(NL_IN_WORD.replacement, text)
    return NL_IN_SENTENCE.pattern.sub(NL_IN_SENTENCE.replacement, text)


def remove_pdf_line_breaks(text: str) -> str:
    """Handle PDF-specific line-wrap breaks and bullet points.

    Args:
        text: The text string to clean.

    Returns:
        The cleaned text with repaired PDF line breaks.
    """
    if "\n" not in text:
        return text
    text = NL_BEFORE_BULLET.pattern.sub(NL_BEFORE_BULLET.replacement, text)
    text = PDF_NEW_LINE_MID_SENTENCE.pattern.sub(
        PDF_NEW_LINE_MID_SENTENCE.replacement, text
    )
    return PDF_NEW_LINE_MID_SENTENCE_NOSPACE.pattern.sub(
        PDF_NEW_LINE_MID_SENTENCE_NOSPACE.replacement, text
    )


def replace_newlines(text: str, doc_type: str = "") -> str:
    """Normalize newlines based on document type (standard or PDF).

    Args:
        text: The text string to process.
        doc_type: Document format override. Defaults to "".

    Returns:
        The text with all line endings normalized.
    """
    if "\n" not in text:
        return text

    if doc_type == "pdf":
        return remove_pdf_line_breaks(text)

    text = remove_newline_in_middle_of_sentence(text)
    text = DOUBLE_NL_SPACE.pattern.sub(DOUBLE_NL_SPACE.replacement, text)
    text = DOUBLE_NL.pattern.sub(DOUBLE_NL.replacement, text)
    text = NL_BEFORE_PERIOD.pattern.sub(NL_BEFORE_PERIOD.replacement, text)
    return NL_TO_CR.pattern.sub(NL_TO_CR.replacement, text)


def replace_escaped_newlines(text: str) -> str:
    """Normalize escaped newline and carriage-return strings.

    Args:
        text: The text string to clean.

    Returns:
        The text with standard unescaped line endings.
    """
    if "\\" not in text:
        return text
    text = ESCAPED_NL.pattern.sub(ESCAPED_NL.replacement, text)
    text = ESCAPED_CR.pattern.sub(ESCAPED_CR.replacement, text)
    text = TYPO_ESCAPED_NL.pattern.sub(TYPO_ESCAPED_NL.replacement, text)
    return TYPO_ESCAPED_CR.pattern.sub(TYPO_ESCAPED_CR.replacement, text)


def normalize(
    text: str | None,
    *,
    config: LanguageProtocol | None = None,
    doc_type: str = "",
    char_span: bool = False,
    custom_rules: Sequence[Rule] = (),
) -> str | None:
    """Run the complete normalization and cleaning pipeline on input text.

    If char_span is True, destructive normalizers are bypassed to preserve exact
    source offsets.

    Args:
        text: The text to normalize.
        config: A language configuration module implementing LanguageProtocol. Defaults to None.
        doc_type: Document format, e.g. "pdf". Defaults to "".
        char_span: If True, destructive normalizations are bypassed. Defaults to False.
        custom_rules: Custom cleaning rules to apply. Defaults to ().

    Returns:
        The fully cleaned and normalized string, or None if input was None.
    """
    if text is None:
        return None
    if not text:
        return ""
    if char_span:
        return text

    cleaned = strip_html(text)
    cleaned = clean_inline_formatting(cleaned)
    cleaned = clean_quotations(cleaned)
    cleaned = clean_table_of_contents(cleaned)
    cleaned = clean_consecutive_characters(cleaned)
    cleaned = check_for_no_space_in_between_sentences(cleaned)

    # Combine custom rules and config clean rules
    rules: tuple[Rule, ...] = tuple(custom_rules)
    if config is not None and config.clean_rules:
        rules = rules + config.clean_rules

    for rule in rules:
        cleaned = rule.pattern.sub(rule.replacement, cleaned)

    cleaned = replace_newlines(cleaned, doc_type=doc_type)
    cleaned = replace_escaped_newlines(cleaned)

    return cleaned
