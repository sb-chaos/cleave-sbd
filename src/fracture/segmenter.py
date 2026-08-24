"""Public API layer for sentence boundary disambiguation and segmentation."""

import re
from collections.abc import Generator
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

    def stream(
        self, text: str = "", *, chunk_paragraphs: int = 1000
    ) -> Generator[str | TextSpan, None, None]:
        """Lazily stream sentences or TextSpan objects with bounded memory usage.

        Splits on natural paragraph boundaries and yields sentences incrementally per chunk.

        Args:
            text: The input text to segment. Defaults to "".
            chunk_paragraphs: Number of paragraphs held in each chunk. Defaults to 1000.

        Yields:
            Sentence strings, or TextSpan objects if char_span is True.
        """
        if not text or text.isspace():
            return

        if chunk_paragraphs < 1:
            raise ValueError("chunk_paragraphs must be at least 1")

        paragraph_pattern = re.compile(r"(?:\r?\n){2,}")
        matches = list(paragraph_pattern.finditer(text))
        if not matches:
            yield from self.segment(text)
            return

        text_len = len(text)
        para_count = 0
        chunk_start = 0

        for match in matches:
            para_count += 1
            if para_count == chunk_paragraphs:
                p_end = match.start()
                if p_end > chunk_start:
                    chunk = text[chunk_start:p_end]
                    if self.char_span:
                        spans = self.segment(chunk)
                        for j, item in enumerate(spans):
                            if isinstance(item, TextSpan):
                                if j + 1 == len(spans):
                                    span_end = item.end + (match.end() - p_end)
                                    raw_slice = text[
                                        chunk_start + item.start : chunk_start
                                        + span_end
                                    ]
                                    yield TextSpan(
                                        sent=unmask_all(raw_slice),
                                        start=chunk_start + item.start,
                                        end=chunk_start + span_end,
                                    )
                                else:
                                    yield TextSpan(
                                        sent=item.sent,
                                        start=chunk_start + item.start,
                                        end=chunk_start + item.end,
                                    )
                    else:
                        yield from self.segment(chunk)
                chunk_start = match.end()
                para_count = 0

        if chunk_start < text_len:
            chunk = text[chunk_start:text_len]
            if self.char_span:
                for item in self.segment(chunk):
                    if isinstance(item, TextSpan):
                        yield TextSpan(
                            sent=item.sent,
                            start=chunk_start + item.start,
                            end=chunk_start + item.end,
                        )
            else:
                yield from self.segment(chunk)
