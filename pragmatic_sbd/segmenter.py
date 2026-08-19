"""Public API layer for sentence boundary disambiguation and segmentation."""

import re
from dataclasses import dataclass

from pragmatic_sbd.cleaner import Cleaner
from pragmatic_sbd.lang import get_language_module
from pragmatic_sbd.lang.common import unmask_all
from pragmatic_sbd.processor import Processor


@dataclass(slots=True, frozen=True)
class TextSpan:
    """A data class representing a span of text with character offsets."""

    sent: str
    start: int
    end: int

    def __repr__(self) -> str:
        return self.sent

    def __eq__(self, ts: object) -> bool:
        if isinstance(ts, TextSpan):
            return self.sent == ts.sent and self.start == ts.start and self.end == ts.end
        return False


Text = TextSpan


@dataclass(slots=True, frozen=True)
class Segmenter:
    """Splits input text into sentences with optional cleaning and character offset spans.

    Args:
        language (str): Two-letter ISO 639-1 code specifying the language of the text.
            Defaults to "en".
        clean (bool, optional): Whether to clean the text before segmentation. Defaults to False.
        doc_type (str, optional): Type of document. Use 'pdf' for OCR-extracted text. Defaults to "".
        char_span (bool, optional): If True, includes start and end character offsets for each
            sentence in the original text. Defaults to False.

    Raises:
        ValueError: If `clean` is True and `char_span` is also True.
        ValueError: If `doc_type` is 'pdf' but `clean` is False.
    """

    language: str = "en"
    clean: bool = False
    doc_type: str = ""
    char_span: bool = False

    def __post_init__(self) -> None:
        if self.clean and self.char_span:
            raise ValueError(
                "char_span must be False if clean is True. Since `clean=True` will modify original text."
            )
        if self.doc_type == "pdf" and not self.clean:
            raise ValueError(
                "`doc_type='pdf'` should have `clean=True` & "
                "`char_span` should be False since original"
                "text will be modified."
            )
        if self.language:
            get_language_module(self.language)

    def segment(self, text: str = "") -> list[str] | list[TextSpan]:
        """Segment the input text into a list of sentences or TextSpan objects."""
        if not text or not text.strip():
            return []

        if self.clean:
            cleaned_text = Cleaner(
                text=text,
                lang=self.language,
                doc_type=self.doc_type,
                char_span=False,
            ).clean()
            sentences = Processor(
                text=cleaned_text or "",
                lang=self.language,
                char_span=False,
            ).process()
            return [unmask_all(s) for s in sentences]

        sentences = Processor(
            text=text,
            lang=self.language,
            char_span=self.char_span,
        ).process()

        if self.char_span:
            return self.sentences_with_char_spans(text, sentences)

        return [unmask_all(s) for s in sentences]

    def sentences_with_char_spans(self, original_text: str, sentences: list[str]) -> list[TextSpan]:
        """Calculate start and end character offsets sequentially against the original source text."""
        sent_spans: list[TextSpan] = []
        prior_end_char_idx: int = 0
        for sent in sentences:
            pattern = re.compile(rf"{re.escape(sent)}\s*")
            match = pattern.search(original_text, pos=prior_end_char_idx)
            if match:
                sent_spans.append(
                    TextSpan(
                        sent=unmask_all(match.group(0)),
                        start=match.start(),
                        end=match.end(),
                    )
                )
                prior_end_char_idx = match.end()
        return sent_spans
