"""Public API layer for sentence boundary disambiguation and segmentation."""

import re
from collections.abc import Generator
from dataclasses import dataclass
from typing import cast

from csbd.disambiguator import disambiguate
from csbd.language import get_language_module
from csbd.models import OffsetMap, TextSpan
from csbd.normalizer import normalize_with_map
from csbd.rules import is_boundary_whitespace, unmask_all

__all__ = [
    "Segmenter",
]


@dataclass(slots=True, frozen=True)
class Segmenter:
    """Splits input text into sentences with optional cleaning and character offset spans.

    Args:
        language (str): Two-letter ISO 639-1 code specifying the language of the text.
            Defaults to "en".
        clean (bool, optional): Whether to clean the text before segmentation. Defaults to False.
        doc_type (str, optional): Type of document. Use 'pdf' for OCR-extracted text. Defaults to "".
        char_span (bool, optional): If True, includes start and end character offsets for each
            sentence mapped back to the original source text. Defaults to False.

    Raises:
        ValueError: If `doc_type` is 'pdf' but `clean` is False.
    """

    language: str = "en"
    clean: bool = False
    doc_type: str = ""
    char_span: bool = False

    def __post_init__(self) -> None:
        if self.doc_type == "pdf" and not self.clean:
            raise ValueError(
                "`doc_type='pdf'` requires `clean=True` to normalize PDF line breaks."
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
        offset_map: OffsetMap | None = None

        if self.clean:
            norm_res = normalize_with_map(
                text=text,
                config=config,
                doc_type=self.doc_type,
            )
            target_text = norm_res.text
            offset_map = norm_res.offset_map
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
            for i, (c_start, c_end) in enumerate(spans):
                next_start = spans[i + 1][0] if i + 1 < len(spans) else text_len
                span_end = c_end
                while span_end < next_start and is_boundary_whitespace(
                    target_text[span_end]
                ):
                    span_end += 1

                raw_clean_slice = target_text[c_start:span_end]
                clean_sent = unmask_all(raw_clean_slice)

                if offset_map is not None:
                    raw_start, raw_end = offset_map.clean_span_to_raw_span(
                        c_start, span_end
                    )
                    raw_slice_str = text[raw_start:raw_end]
                    result_spans.append(
                        TextSpan(
                            sent=clean_sent,
                            start=raw_start,
                            end=raw_end,
                            clean_start=c_start,
                            clean_end=span_end,
                            raw_slice=raw_slice_str,
                        )
                    )
                else:
                    result_spans.append(
                        TextSpan(
                            sent=clean_sent,
                            start=c_start,
                            end=span_end,
                            clean_start=c_start,
                            clean_end=span_end,
                            raw_slice=text[c_start:span_end],
                        )
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
        text_len = len(text)
        para_count = 0
        chunk_start = 0
        has_match = False

        for match in paragraph_pattern.finditer(text):
            has_match = True
            para_count += 1
            if para_count == chunk_paragraphs:
                chunk_end = match.end()
                if chunk_end > chunk_start:
                    chunk = text[chunk_start:chunk_end]
                    delim = text[match.start() : match.end()]
                    if self.char_span:
                        spans = self.segment(chunk)
                        num_spans = len(spans)
                        for j, item in enumerate(spans):
                            if isinstance(item, TextSpan):
                                is_last = j + 1 == num_spans
                                yield TextSpan(
                                    sent=item.sent,
                                    start=chunk_start + item.start,
                                    end=chunk_start + item.end,
                                    clean_start=item.clean_start,
                                    clean_end=item.clean_end,
                                    raw_slice=item.raw_slice,
                                    trailing_delim=delim if is_last else "",
                                )
                    else:
                        yield from self.segment(chunk)
                chunk_start = chunk_end
                para_count = 0

        if not has_match:
            yield from self.segment(text)
            return

        if chunk_start < text_len:
            chunk = text[chunk_start:text_len]
            if self.char_span:
                for item in self.segment(chunk):
                    if isinstance(item, TextSpan):
                        yield TextSpan(
                            sent=item.sent,
                            start=chunk_start + item.start,
                            end=chunk_start + item.end,
                            clean_start=item.clean_start,
                            clean_end=item.clean_end,
                            raw_slice=item.raw_slice,
                            trailing_delim="",
                        )
            else:
                yield from self.segment(chunk)
