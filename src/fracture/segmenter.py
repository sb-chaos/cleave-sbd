"""Public API layer for sentence boundary disambiguation and segmentation."""

from collections.abc import Sequence
from dataclasses import dataclass

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

        if self.clean:
            cleaned_text: str | None = normalize(
                text=text,
                config=config,
                doc_type=self.doc_type,
                char_span=False,
            )
            sentences = disambiguate(
                text=cleaned_text or "",
                config=config,
                char_span=False,
            )
            return tuple(unmask_all(sentence) for sentence in sentences)

        sentences = disambiguate(
            text=text,
            config=config,
            char_span=self.char_span,
        )

        if self.char_span:
            return self.sentences_with_char_spans(text, sentences)

        return tuple(unmask_all(sentence) for sentence in sentences)

    def sentences_with_char_spans(
        self, original_text: str, sentences: Sequence[str]
    ) -> tuple[TextSpan, ...]:
        """Calculate start and end character offsets sequentially against the original source text.

        Args:
            original_text: The original, unmodified text.
            sentences: Segmented sentence strings to locate.

        Returns:
            A tuple of TextSpan objects containing the sentences and their start/end offsets.
        """
        sent_spans: list[TextSpan] = []
        prior_end_char_idx: int = 0
        orig_len: int = len(original_text)

        for sent in sentences:
            start_idx = original_text.find(sent, prior_end_char_idx)
            if start_idx == -1:
                continue
            end_idx = start_idx + len(sent)
            while end_idx < orig_len and original_text[end_idx].isspace():
                end_idx += 1

            sent_spans.append(
                TextSpan(
                    sent=original_text[start_idx:end_idx],
                    start=start_idx,
                    end=end_idx,
                )
            )
            prior_end_char_idx = end_idx

        return tuple(sent_spans)
