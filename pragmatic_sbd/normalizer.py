"""Stateless normalization and cleaning pipeline for text segmentation."""

import re
from collections.abc import Sequence
from dataclasses import dataclass
from types import ModuleType

from pragmatic_sbd.lang import LanguageConfig, get_language_module
from pragmatic_sbd.lang.common import Rule

URL_EMAIL_KEYWORDS: tuple[str, ...] = (
    ".com",
    ".net",
    ".org",
    ".io",
    ".gov",
    ".edu",
    "http://",
    "https://",
    "@",
    "www.",
)

# Text & Whitespace Normalization Rules
NL_IN_WORD: Rule = Rule(re.compile(r"\n(?=[a-zA-Z]{1,2}\n)"))
DOUBLE_NL_SPACE: Rule = Rule(re.compile(r"\n \n"), "\r")
DOUBLE_NL: Rule = Rule(re.compile(r"\n\n"), "\r")
NL_BEFORE_PERIOD: Rule = Rule(re.compile(r"\n(?=\.(\s|\n))"))
NL_TO_CR: Rule = Rule(re.compile(r"\n"), "\r")
ESCAPED_NL: Rule = Rule(re.compile(r"\\n"), "\n")
ESCAPED_CR: Rule = Rule(re.compile(r"\\r"), "\r")
TYPO_ESCAPED_NL: Rule = Rule(re.compile(r"\\\ n"), "\n")
TYPO_ESCAPED_CR: Rule = Rule(re.compile(r"\\\ r"), "\r")
INLINE_FORMATTING: Rule = Rule(re.compile(r"{b\^&gt;\d*&lt;b\^}|{b\^>\d*<b\^}"))
TABLE_OF_CONTENTS: Rule = Rule(re.compile(r"\.{4,}\s*\d+-*\d*"), "\r")
CONSECUTIVE_PERIODS: Rule = Rule(re.compile(r"\.{5,}"), " ")
CONSECUTIVE_SLASHES: Rule = Rule(re.compile(r"/{3}"))
NO_SPACE_SENTENCE_COMBINED: re.Pattern[str] = re.compile(r"(?<=[a-z\d])\.(?=[A-Z])")
NL_IN_SENTENCE: Rule = Rule(re.compile(r"(?<=\s)\n(?=([a-z]|\())"))
NL_BEFORE_BULLET: Rule = Rule(re.compile(r"\n(?=•)"), "\r")
NORMAL_QUOTES: Rule = Rule(re.compile(r"''|``"), '"')

# HTML Rules
HTML_TAG_RULE: Rule = Rule(
    re.compile(r"<\/?\w+((\s+\w+(\s*=\s*(?:\".*?\"|'.*?'|[\^'\">\s]+))?)+\s*|\s*)\/?>")
)
HTML_ESCAPED_TAG_RULE: Rule = Rule(re.compile(r"&lt;\/?[^gt;]*gt;"))
HTML_RULES: tuple[Rule, ...] = (HTML_TAG_RULE, HTML_ESCAPED_TAG_RULE)

# PDF Rules
PDF_NEW_LINE_MID_SENTENCE: Rule = Rule(re.compile(r"(?<=[^\n]\s)\n(?=\S)"))
PDF_NEW_LINE_MID_SENTENCE_NOSPACE: Rule = Rule(re.compile(r"\n(?=[a-z])"), " ")


def _replace_no_space_sentence(match: re.Match[str]) -> str:
    start = match.start()
    text = match.string

    word_start = start
    while word_start > 0 and text[word_start - 1] not in " \n\r\t":
        word_start -= 1

    word_end = start + 1
    text_len = len(text)
    while word_end < text_len and text[word_end] not in " \n\r\t":
        word_end += 1

    word = text[word_start:word_end].lower()
    if any(keyword in word for keyword in URL_EMAIL_KEYWORDS):
        return match.group(0)
    return ". "


@dataclass(slots=True)
class Normalizer:
    """Stateless text normalizer and cleaner.

    Transforms text through a sequence of pure (text: str) -> str cleaning stages
    prior to sentence boundary disambiguation.

    Args:
        text: The default text string to clean. Defaults to "".
        lang: Two-letter ISO code or language module. Defaults to "".
        doc_type: Document format, e.g. "pdf". Defaults to "".
        char_span: If True, destructive normalizations are bypassed. Defaults to False.
        rules: Custom cleaning rules to apply. Defaults to ().
    """

    text: str | None = None
    lang: str | ModuleType | LanguageConfig = ""
    doc_type: str = ""
    char_span: bool = False
    rules: Sequence[Rule] = ()

    def __post_init__(self) -> None:
        lang_module = get_language_module(self.lang) if self.lang else None
        lang_clean_rules: tuple[Rule, ...] = (
            lang_module.clean_rules if lang_module is not None else ()
        )
        if lang_clean_rules:
            self.rules = tuple(self.rules) + lang_clean_rules
        elif not isinstance(self.rules, tuple):
            self.rules = tuple(self.rules)

    def normalize(self, text: str | None = None) -> str | None:
        """Run the complete normalization and cleaning pipeline on input text.

        If char_span is True, destructive normalizers are bypassed to preserve exact
        source offsets.

        Args:
            text: The text to normalize. If not provided, uses the instance's text.

        Returns:
            The fully cleaned and normalized string, or None if input was None.
        """
        target = self.text if text is None else text
        if target is None:
            return None
        if not target:
            return ""
        if self.char_span:
            return target

        cleaned = self.strip_html(target)
        cleaned = self.clean_inline_formatting(cleaned)
        cleaned = self.clean_quotations(cleaned)
        cleaned = self.clean_table_of_contents(cleaned)
        cleaned = self.clean_consecutive_characters(cleaned)
        cleaned = self.check_for_no_space_in_between_sentences(cleaned)

        for rule in self.rules:
            cleaned = rule.pattern.sub(rule.replacement, cleaned)

        cleaned = self.replace_newlines(cleaned, doc_type=self.doc_type)
        cleaned = self.replace_escaped_newlines(cleaned)

        return cleaned

    @staticmethod
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
            text = HTML_ESCAPED_TAG_RULE.pattern.sub(HTML_ESCAPED_TAG_RULE.replacement, text)
        return text

    @staticmethod
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

    @staticmethod
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

    @staticmethod
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

    @staticmethod
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

    @staticmethod
    def check_for_no_space_in_between_sentences(text: str) -> str:
        """Insert spaces in punctuation-joined sentences while protecting URLs/emails.

        Args:
            text: The text string to clean.

        Returns:
            The text with spaces inserted after punctuation marks where required.
        """
        if "." not in text:
            return text
        return NO_SPACE_SENTENCE_COMBINED.sub(_replace_no_space_sentence, text)

    @staticmethod
    def remove_newline_in_middle_of_sentence(text: str) -> str:
        """Remove mid-sentence line breaks within words and clauses.

        Args:
            text: The text string to clean.

        Returns:
            The text with mid-sentence line breaks removed.
        """
        text = NL_IN_WORD.pattern.sub(NL_IN_WORD.replacement, text)
        return NL_IN_SENTENCE.pattern.sub(NL_IN_SENTENCE.replacement, text)

    @staticmethod
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
        text = PDF_NEW_LINE_MID_SENTENCE.pattern.sub(PDF_NEW_LINE_MID_SENTENCE.replacement, text)
        return PDF_NEW_LINE_MID_SENTENCE_NOSPACE.pattern.sub(
            PDF_NEW_LINE_MID_SENTENCE_NOSPACE.replacement, text
        )

    def replace_newlines(self, text: str, doc_type: str | None = None) -> str:
        """Normalize newlines based on document type (standard or PDF).

        Args:
            text: The text string to process.
            doc_type: Document format override. Defaults to self.doc_type.

        Returns:
            The text with all line endings normalized.
        """
        if "\n" not in text:
            return text

        if (doc_type or self.doc_type) == "pdf":
            return self.remove_pdf_line_breaks(text)

        text = self.remove_newline_in_middle_of_sentence(text)
        text = DOUBLE_NL_SPACE.pattern.sub(DOUBLE_NL_SPACE.replacement, text)
        text = DOUBLE_NL.pattern.sub(DOUBLE_NL.replacement, text)
        text = NL_BEFORE_PERIOD.pattern.sub(NL_BEFORE_PERIOD.replacement, text)
        return NL_TO_CR.pattern.sub(NL_TO_CR.replacement, text)

    @staticmethod
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
