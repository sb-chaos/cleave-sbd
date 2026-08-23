"""Core Segmenter API, character offset tracking, PDF mode, and edge case tests."""

from __future__ import annotations

from pathlib import Path
from typing import Final, cast

import pytest

import fracture
from fracture.segmenter import TextSpan
from tests.loaders import load_pdf_cases
from tests.models import PdfTestCase

PDF_CASES: Final[list[PdfTestCase]] = load_pdf_cases()


@pytest.mark.parametrize("empty_input", ["", None, "\n"])
def test_segmenter_empty_inputs(empty_input: str | None) -> None:
    """Verify segmenter returns an empty list for empty/null inputs."""
    seg = fracture.Segmenter(language="en", clean=False, char_span=False)
    assert seg.segment(empty_input or "") == []


def test_segmenter_immutability() -> None:
    """Verify segmenter does not mutate input strings."""
    text = "My name is Jonas E. Smith. Please turn to p. 55."
    seg = fracture.Segmenter(language="en", clean=False, char_span=False)
    _ = seg.segment(text)
    assert text == "My name is Jonas E. Smith. Please turn to p. 55."


def test_sbd_char_span_basic() -> None:
    """Verify character offset span calculation."""
    text = "My name is Jonas E. Smith. Please turn to p. 55."
    seg = fracture.Segmenter(language="en", clean=False, char_span=True)
    raw_segments = seg.segment(text)
    segments = cast(list[TextSpan], raw_segments)
    expected = [
        TextSpan(sent="My name is Jonas E. Smith. ", start=0, end=27),
        TextSpan(sent="Please turn to p. 55.", start=27, end=48),
    ]
    assert segments == expected
    assert text == "".join(s.sent for s in segments)


def test_same_sentence_different_char_span() -> None:
    """Verify correct character offset tracking for duplicate sentences."""
    text = (
        "From the AP comes this story :\n"
        "President Bush on Tuesday nominated two individuals to replace retiring jurists on federal courts in the Washington area.\n"
        "***\n"
        "After you are elected in 2004, what will your memoirs say about you, what will the title be, and what will the main theme say?\n"
        "***\n"
        '"THE PRESIDENT: I appreciate that.\n'
        "(Laughter.)\n"
        "My life is too complicated right now trying to do my job.\n"
        "(Laughter.)"
    )
    expected_text_spans = [
        TextSpan(sent="From the AP comes this story :\n", start=0, end=31),
        TextSpan(
            sent="President Bush on Tuesday nominated two individuals to replace retiring jurists on federal courts in the Washington area.\n",
            start=31,
            end=153,
        ),
        TextSpan(sent="***\n", start=153, end=157),
        TextSpan(
            sent="After you are elected in 2004, what will your memoirs say about you, what will the title be, and what will the main theme say?\n",
            start=157,
            end=284,
        ),
        TextSpan(sent="***\n", start=284, end=288),
        TextSpan(sent='"THE PRESIDENT: I appreciate that.\n', start=288, end=323),
        TextSpan(sent="(Laughter.)\n", start=323, end=335),
        TextSpan(
            sent="My life is too complicated right now trying to do my job.\n",
            start=335,
            end=393,
        ),
        TextSpan(sent="(Laughter.)", start=393, end=404),
    ]
    seg = fracture.Segmenter(language="en", clean=False, char_span=True)
    raw_segments = seg.segment(text)
    segments = cast(list[TextSpan], raw_segments)
    assert segments == expected_text_spans
    assert text == "".join(s.sent for s in segments)


def test_exception_with_both_clean_and_span_true() -> None:
    """Verify ValueError when both clean and char_span are True."""
    with pytest.raises(ValueError) as excinfo:
        _ = fracture.Segmenter(language="en", clean=True, char_span=True)
    assert "char_span must be False if clean is True" in str(excinfo.value)


def test_exception_with_doc_type_pdf_and_clean_false() -> None:
    """Verify ValueError when doc_type is pdf but clean is False."""
    with pytest.raises(ValueError) as excinfo:
        _ = fracture.Segmenter(language="en", clean=False, doc_type="pdf")
    assert "`doc_type='pdf'` should have `clean=True`" in str(excinfo.value)


def test_exception_with_doc_type_pdf_and_both_clean_char_span_true() -> None:
    """Verify ValueError when doc_type is pdf with char_span True."""
    with pytest.raises(ValueError) as excinfo:
        _ = fracture.Segmenter(
            language="en", clean=True, doc_type="pdf", char_span=True
        )
    assert "char_span must be False if clean is True" in str(excinfo.value)


@pytest.mark.parametrize("case", PDF_CASES)
def test_pdf_segmentation(case: PdfTestCase) -> None:
    """Verify sentence boundary segmentation on PDF documents."""
    seg = fracture.Segmenter(language="en", clean=True, doc_type="pdf")
    raw_segments = seg.segment(case.text)
    segments = cast(list[str], raw_segments)
    stripped: list[str] = [s.strip() for s in segments]
    assert stripped == list(case.expected)


def test_file_segmenter(tmp_path: Path) -> None:
    """Verify file-based text segmentation and numbered output formatting."""
    input_file = tmp_path / "sample_input.txt"
    output_file = tmp_path / "sample_output.txt"
    sample_content = (
        "Hello world! This is the first test sentence. My name is Dr. Jonas E. Smith "
        "and I work in Washington, D.C. at 10.5% growth rate. Is this sentence number four?\n\n"
        "Here begins a new paragraph. Please refer to Fig. 1.2 on p. 45 for further details. "
        '"We will succeed!" said the director. The end.'
    )
    input_file.write_text(sample_content, encoding="utf-8")

    text = input_file.read_text(encoding="utf-8")
    segmenter = fracture.Segmenter(language="en", clean=True, char_span=False)
    raw_segments = segmenter.segment(text)
    sentences = cast(list[str], raw_segments)

    output_lines: list[str] = [
        f"=== fracture Segmentation Output ({len(sentences)} Sentences) ===",
        f"Input File : {input_file.as_posix()}",
        "=" * 60,
    ]
    for idx, sent in enumerate(sentences, start=1):
        output_lines.append(f"[{idx}] {sent}")

    output_file.write_text("\n".join(output_lines), encoding="utf-8")

    assert len(sentences) > 0
    assert output_file.exists()
    content = output_file.read_text(encoding="utf-8")
    assert "[1]" in content
    assert "=== fracture Segmentation Output" in content
