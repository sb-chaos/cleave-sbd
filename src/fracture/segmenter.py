"""Public API layer for sentence boundary disambiguation and segmentation."""

from dataclasses import dataclass
from typing import cast

from fracture.disambiguator import disambiguate
from fracture.language import get_language_module
from fracture.normalizer import normalize
from fracture.rules import unmask_all


@dataclass(slots=True, frozen=True)
class TextSpan:
    """A data class representing a span of text with character offsets."""

    sent: str
    start: int
    end: int

    def __repr__(self) -> str:
        return self.sent

    def __eq__(self, other: object) -> bool:
        if isinstance(other, TextSpan):
            return (
                self.sent == other.sent
                and self.start == other.start
                and self.end == other.end
            )
        return False


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

    def segment(self, text: str = "") -> tuple[str, ...] | tuple[TextSpan, ...]:
        """Segment the input text into a sequence of sentences or TextSpan objects.

        Args:
            text: The raw text string to segment. Defaults to "".

        Returns:
            A tuple of sentence strings, or TextSpan objects if char_span is True.
        """
        if not text or text.isspace():
            return ()

        config = get_language_module(self.language) if self.language else None

        target_text = text
        if self.clean:
            cleaned = normalize(
                text=text,
                config=config,
                doc_type=self.doc_type,
                char_span=False,
            )
            target_text = cleaned or ""
            if not target_text or target_text.isspace():
                return ()

        output = disambiguate(
            text=target_text,
            config=config,
            char_span=self.char_span,
        )

        if not output:
            return ()

        if self.char_span:
            spans = cast(tuple[tuple[int, int], ...], output)
            text_len = len(target_text)
            result_spans: list[TextSpan] = []
            for i, (start, end) in enumerate(spans):
                next_start = spans[i + 1][0] if i + 1 < len(spans) else text_len
                span_end = end
                while span_end < next_start and target_text[span_end].isspace():
                    span_end += 1

                raw_slice = target_text[start:span_end]
                clean_sent = unmask_all(raw_slice)
                result_spans.append(
                    TextSpan(sent=clean_sent, start=start, end=span_end)
                )
            return tuple(result_spans)

        return cast(tuple[str, ...], output)
