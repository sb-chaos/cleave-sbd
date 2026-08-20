"""Public API layer for sentence boundary disambiguation and segmentation."""

<<<<<<< HEAD
from dataclasses import dataclass

from pragmatic_sbd.disambiguator import Disambiguator
from pragmatic_sbd.lang import get_language_module
from pragmatic_sbd.lang.common import unmask_all
from pragmatic_sbd.normalizer import Normalizer
=======
import re
from dataclasses import dataclass

from pragmatic_sbd.cleaner import Cleaner
from pragmatic_sbd.lang.common.standard import unmask_all
from pragmatic_sbd.languages import get_language_module
from pragmatic_sbd.processor import Processor
>>>>>>> add-type-annotations


@dataclass(slots=True, frozen=True)
class TextSpan:
    """A data class representing a span of text with character offsets."""

    sent: str
    start: int
    end: int

    def __repr__(self) -> str:
        return self.sent

<<<<<<< HEAD
    def __eq__(self, other: object) -> bool:
        if isinstance(other, TextSpan):
            return self.sent == other.sent and self.start == other.start and self.end == other.end
        return False


@dataclass(slots=True, frozen=True)
=======
    def __eq__(self, ts: object) -> bool:
        if isinstance(ts, TextSpan):
            return self.sent == ts.sent and self.start == ts.start and self.end == ts.end
        return False


Text = TextSpan


>>>>>>> add-type-annotations
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

<<<<<<< HEAD
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
=======
    def __init__(
        self,
        language: str = "en",
        clean: bool = False,
        doc_type: str = "",
        char_span: bool = False,
    ) -> None:
        if clean and char_span:
            raise ValueError(
                "char_span must be False if clean is True. Since `clean=True` will modify original text."
            )
        if doc_type == "pdf" and not clean:
>>>>>>> add-type-annotations
            raise ValueError(
                "`doc_type='pdf'` should have `clean=True` & "
                "`char_span` should be False since original"
                "text will be modified."
            )
<<<<<<< HEAD
=======

        self.language: str = language
        self.clean: bool = clean
        self.doc_type: str = doc_type
        self.char_span: bool = char_span
>>>>>>> add-type-annotations
        if self.language:
            get_language_module(self.language)

    def segment(self, text: str = "") -> list[str] | list[TextSpan]:
<<<<<<< HEAD
        """Segment the input text into a list of sentences or TextSpan objects.

        Args:
            text: The raw text string to segment. Defaults to "".

        Returns:
            A list of sentence strings, or TextSpan objects if char_span is True.
        """
        if not text or text.isspace():
            return []

        if self.clean:
            cleaned_text = Normalizer(
=======
        """Segment the input text into a list of sentences or TextSpan objects."""
        if not text or not text.strip():
            return []

        if self.clean:
            cleaned_text = Cleaner(
>>>>>>> add-type-annotations
                text=text,
                lang=self.language,
                doc_type=self.doc_type,
                char_span=False,
<<<<<<< HEAD
            ).normalize()
            sentences = Disambiguator(
                text=cleaned_text or "",
                lang=self.language,
                char_span=False,
            ).disambiguate()
            return [unmask_all(sentence) for sentence in sentences]

        sentences = Disambiguator(
            text=text,
            lang=self.language,
            char_span=self.char_span,
        ).disambiguate()
=======
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
>>>>>>> add-type-annotations

        if self.char_span:
            return self.sentences_with_char_spans(text, sentences)

<<<<<<< HEAD
        return [unmask_all(sentence) for sentence in sentences]

    def sentences_with_char_spans(self, original_text: str, sentences: list[str]) -> list[TextSpan]:
        """Calculate start and end character offsets sequentially against the original source text.

        Args:
            original_text: The original, unmodified text.
            sentences: Segmented sentence strings to locate.

        Returns:
            A list of TextSpan objects containing the sentences and their start/end offsets.
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

=======
        return [unmask_all(s) for s in sentences]

    def sentences_with_char_spans(self, original_text: str, sentences: list[str]) -> list[TextSpan]:
        """Calculate start and end character offsets against the original source text."""
        sent_spans: list[TextSpan] = []
        prior_end_char_idx: int = 0
        for sent in sentences:
            for match in re.finditer(rf"{re.escape(sent)}\s*", original_text):
                match_str = match.group(0)
                match_start_idx, match_end_idx = match.span()
                if match_end_idx > prior_end_char_idx:
                    sent_spans.append(
                        TextSpan(
                            sent=unmask_all(match_str),
                            start=match_start_idx,
                            end=match_end_idx,
                        )
                    )
                    prior_end_char_idx = match_end_idx
                    break
>>>>>>> add-type-annotations
        return sent_spans
