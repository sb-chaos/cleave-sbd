"""Stateless normalization and cleaning pipeline for text segmentation."""

from collections.abc import Sequence

from pragmatic_sbd.clean.rules import HTML, PDF, CleanRules as cr
from pragmatic_sbd.lang.common.standard import Rule

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


class Cleaner:
    """Stateless text normalizer and cleaner.

    Transforms text through a sequence of pure (text: str) -> str cleaning stages
    prior to sentence boundary disambiguation.
    """

    def __init__(
        self,
        text: str | None = "",
        lang: str = "",
        doc_type: str = "",
        char_span: bool = False,
        rules: Sequence[Rule] = (),
    ) -> None:
        self.text: str | None = text
        self.lang: str = lang
        self.doc_type: str = doc_type
        self.char_span: bool = char_span
        self.rules: tuple[Rule, ...] = tuple(rules)

    def clean(self, text: str | None = None) -> str | None:
        """Run the complete cleaning pipeline on input text.

        If char_span is True, destructive cleaners are bypassed to preserve exact
        source offsets.
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
        cleaned = self.replace_newlines(cleaned, doc_type=self.doc_type)
        cleaned = self.replace_escaped_newlines(cleaned)

        for rule in self.rules:
            cleaned = rule.pattern.sub(rule.replacement, cleaned)

        return cleaned

    @staticmethod
    def strip_html(text: str) -> str:
        """Strip HTML tags and escaped HTML entities."""
        for rule in HTML.rules:
            text = rule.pattern.sub(rule.replacement, text)
        return text

    @staticmethod
    def clean_inline_formatting(text: str) -> str:
        """Remove inline formatting tags (e.g. {b^>1<b^})."""
        return cr.INLINE_FORMATTING.pattern.sub(cr.INLINE_FORMATTING.replacement, text)

    @staticmethod
    def clean_quotations(text: str) -> str:
        """Normalize backticks and duplicated quote characters."""
        text = text.replace("`", "'")
        return cr.NORMAL_QUOTES.pattern.sub(cr.NORMAL_QUOTES.replacement, text)

    @staticmethod
    def clean_table_of_contents(text: str) -> str:
        """Clean leader dots in table-of-contents entries."""
        return cr.TABLE_OF_CONTENTS.pattern.sub(cr.TABLE_OF_CONTENTS.replacement, text)

    @staticmethod
    def clean_consecutive_characters(text: str) -> str:
        """Normalize consecutive periods and slashes."""
        text = cr.CONSECUTIVE_PERIODS.pattern.sub(cr.CONSECUTIVE_PERIODS.replacement, text)
        return cr.CONSECUTIVE_SLASHES.pattern.sub(cr.CONSECUTIVE_SLASHES.replacement, text)

    @staticmethod
    def check_for_no_space_in_between_sentences(text: str) -> str:
        """Insert spaces in punctuation-joined sentences while protecting URLs/emails."""
        words = text.split(" ")
        cleaned_words: list[str] = []
        for word in words:
            if any(k in word.lower() for k in URL_EMAIL_KEYWORDS):
                cleaned_words.append(word)
                continue
            w = cr.NO_SPACE_SENTENCE_ALPHA.pattern.sub(cr.NO_SPACE_SENTENCE_ALPHA.replacement, word)
            w = cr.NO_SPACE_SENTENCE_DIGIT.pattern.sub(cr.NO_SPACE_SENTENCE_DIGIT.replacement, w)
            cleaned_words.append(w)
        return " ".join(cleaned_words)

    @staticmethod
    def remove_newline_in_middle_of_sentence(text: str) -> str:
        """Remove mid-sentence line breaks within words and clauses."""
        text = cr.NL_IN_WORD.pattern.sub(cr.NL_IN_WORD.replacement, text)
        return cr.NL_IN_SENTENCE.pattern.sub(cr.NL_IN_SENTENCE.replacement, text)

    @staticmethod
    def remove_pdf_line_breaks(text: str) -> str:
        """Handle PDF-specific line-wrap breaks and bullet points."""
        text = cr.NL_BEFORE_BULLET.pattern.sub(cr.NL_BEFORE_BULLET.replacement, text)
        text = PDF.new_line_mid_sentence.pattern.sub(PDF.new_line_mid_sentence.replacement, text)
        return PDF.new_line_mid_sentence_nospace.pattern.sub(
            PDF.new_line_mid_sentence_nospace.replacement, text
        )

    def replace_newlines(self, text: str, doc_type: str | None = None) -> str:
        """Normalize newlines based on document type (standard or PDF)."""
        if (doc_type or self.doc_type) == "pdf":
            return self.remove_pdf_line_breaks(text)

        text = self.remove_newline_in_middle_of_sentence(text)
        text = cr.DOUBLE_NL_SPACE.pattern.sub(cr.DOUBLE_NL_SPACE.replacement, text)
        text = cr.DOUBLE_NL.pattern.sub(cr.DOUBLE_NL.replacement, text)
        text = cr.NL_BEFORE_PERIOD.pattern.sub(cr.NL_BEFORE_PERIOD.replacement, text)
        return cr.NL_TO_CR.pattern.sub(cr.NL_TO_CR.replacement, text)

    @staticmethod
    def replace_escaped_newlines(text: str) -> str:
        """Normalize escaped newline and carriage-return strings."""
        text = cr.ESCAPED_NL.pattern.sub(cr.ESCAPED_NL.replacement, text)
        text = cr.ESCAPED_CR.pattern.sub(cr.ESCAPED_CR.replacement, text)
        text = cr.TYPO_ESCAPED_NL.pattern.sub(cr.TYPO_ESCAPED_NL.replacement, text)
        return cr.TYPO_ESCAPED_CR.pattern.sub(cr.TYPO_ESCAPED_CR.replacement, text)
