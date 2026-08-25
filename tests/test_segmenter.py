"""Core Segmenter API, character offset tracking, PDF mode, and edge case tests."""

from __future__ import annotations

from pathlib import Path
from typing import Final, cast

import pytest

import csbd
from csbd.models import TextSpan
from tests.loaders import PdfCase, load_pdf_cases

PDF_CASES: Final[list[PdfCase]] = load_pdf_cases()


@pytest.mark.parametrize("empty_input", ["", None, "\n"])
def test_segmenter_empty_inputs(empty_input: str | None) -> None:
    """Verify segmenter returns an empty list for empty/null inputs."""
    seg = csbd.Segmenter(language="en", clean=False, char_span=False)
    assert seg.segment(empty_input or "") == ()


def test_segmenter_immutability() -> None:
    """Verify segmenter does not mutate input strings."""
    text = "My name is Jonas E. Smith. Please turn to p. 55."
    seg = csbd.Segmenter(language="en", clean=False, char_span=False)
    _ = seg.segment(text)
    assert text == "My name is Jonas E. Smith. Please turn to p. 55."


def test_sbd_char_span_basic() -> None:
    """Verify character offset span calculation."""
    text = "My name is Jonas E. Smith. Please turn to p. 55."
    seg = csbd.Segmenter(language="en", clean=False, char_span=True)
    raw_segments = seg.segment(text)
    segments = cast(list[TextSpan], raw_segments)
    expected = [
        TextSpan(
            sent="My name is Jonas E. Smith. ",
            start=0,
            end=27,
            clean_start=0,
            clean_end=27,
            raw_slice="My name is Jonas E. Smith. ",
        ),
        TextSpan(
            sent="Please turn to p. 55.",
            start=27,
            end=48,
            clean_start=27,
            clean_end=48,
            raw_slice="Please turn to p. 55.",
        ),
    ]
    assert tuple(segments) == tuple(expected)
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
        TextSpan(
            sent="From the AP comes this story :\n",
            start=0,
            end=31,
            clean_start=0,
            clean_end=31,
            raw_slice="From the AP comes this story :\n",
        ),
        TextSpan(
            sent="President Bush on Tuesday nominated two individuals to replace retiring jurists on federal courts in the Washington area.\n",
            start=31,
            end=153,
            clean_start=31,
            clean_end=153,
            raw_slice="President Bush on Tuesday nominated two individuals to replace retiring jurists on federal courts in the Washington area.\n",
        ),
        TextSpan(
            sent="***\n",
            start=153,
            end=157,
            clean_start=153,
            clean_end=157,
            raw_slice="***\n",
        ),
        TextSpan(
            sent="After you are elected in 2004, what will your memoirs say about you, what will the title be, and what will the main theme say?\n",
            start=157,
            end=284,
            clean_start=157,
            clean_end=284,
            raw_slice="After you are elected in 2004, what will your memoirs say about you, what will the title be, and what will the main theme say?\n",
        ),
        TextSpan(
            sent="***\n",
            start=284,
            end=288,
            clean_start=284,
            clean_end=288,
            raw_slice="***\n",
        ),
        TextSpan(
            sent='"THE PRESIDENT: I appreciate that.\n',
            start=288,
            end=323,
            clean_start=288,
            clean_end=323,
            raw_slice='"THE PRESIDENT: I appreciate that.\n',
        ),
        TextSpan(
            sent="(Laughter.)\n",
            start=323,
            end=335,
            clean_start=323,
            clean_end=335,
            raw_slice="(Laughter.)\n",
        ),
        TextSpan(
            sent="My life is too complicated right now trying to do my job.\n",
            start=335,
            end=393,
            clean_start=335,
            clean_end=393,
            raw_slice="My life is too complicated right now trying to do my job.\n",
        ),
        TextSpan(
            sent="(Laughter.)",
            start=393,
            end=404,
            clean_start=393,
            clean_end=404,
            raw_slice="(Laughter.)",
        ),
    ]
    seg = csbd.Segmenter(language="en", clean=False, char_span=True)
    raw_segments = seg.segment(text)
    segments = cast(list[TextSpan], raw_segments)
    assert tuple(segments) == tuple(expected_text_spans)
    assert text == "".join(s.sent for s in segments)


def test_clean_and_span_both_true_supported() -> None:
    """Verify clean=True and char_span=True returns clean sentences with exact raw source coordinates."""
    raw_text = "<p>First sentence. Second sentence.</p>"
    seg = csbd.Segmenter(language="en", clean=True, char_span=True)
    raw_spans = seg.segment(raw_text)
    spans = cast(tuple[TextSpan, ...], raw_spans)

    assert len(spans) == 2
    # Clean sentence strings
    assert spans[0].sent.strip() == "First sentence."
    assert spans[1].sent.strip() == "Second sentence."
    # Projected coordinates into raw source text
    assert spans[0].start == 3  # After '<p>'
    assert raw_text[spans[0].start : spans[0].end].startswith("First sentence.")
    assert raw_text[spans[1].start : spans[1].end].startswith("Second sentence.")


def test_clean_and_span_multipass_offset_mapping() -> None:
    """Verify coordinate composition across multiple normalization passes (HTML, quotes, newlines)."""
    raw_text = (
        "<p>First sentence. Second sentence.</p>\n\n"
        "Third sentence with ``quotes'' and <b>tag</b>."
    )
    seg = csbd.Segmenter(language="en", clean=True, char_span=True)
    raw_spans = seg.segment(raw_text)
    spans = cast(tuple[TextSpan, ...], raw_spans)

    assert len(spans) == 3
    # Clean text assertions
    assert spans[0].sent.strip() == "First sentence."
    assert spans[1].sent.strip() == "Second sentence."
    assert spans[2].sent.strip() == 'Third sentence with "quotes" and tag.'

    # Raw span coordinate projection assertions
    assert raw_text[spans[0].start : spans[0].end].startswith("First sentence.")
    assert raw_text[spans[1].start : spans[1].end].startswith("Second sentence.")
    # Third sentence must encompass the full raw slice without truncated tags
    last_slice = raw_text[spans[2].start : spans[2].end]
    assert last_slice.endswith("<b>tag</b>."), (
        f"Expected raw slice to end with '<b>tag</b>.', got {last_slice!r}"
    )


def test_boundary_content_retention_structural_symbols() -> None:
    """Verify structural symbols, markdown dividers, and scene breaks are retained as standalone segments."""
    text = (
        "***\n"
        "First chapter text begins here.\n"
        "---\n"
        "Second chapter text begins here.\n"
        "[...]"
    )
    seg = csbd.Segmenter(language="en", clean=False, char_span=True)
    raw_spans = seg.segment(text)
    spans = cast(tuple[TextSpan, ...], raw_spans)

    assert len(spans) == 5
    assert spans[0].sent.strip() == "***"
    assert spans[0].start == 0
    assert spans[0].end == 4

    assert spans[1].sent.strip() == "First chapter text begins here."
    assert spans[2].sent.strip() == "---"
    assert spans[3].sent.strip() == "Second chapter text begins here."
    assert spans[4].sent.strip() == "[...]"


def test_sentinel_whitespace_boundary_trimming() -> None:
    """Verify leading and trailing PUA space sentinels are stripped cleanly from sentence spans."""
    text = (
        "One further habit which was somewhat weakened . . . "
        "was that of combining words into self-interpreting compounds. . . . "
        "The practice was not abandoned. . . ."
    )
    seg = csbd.Segmenter(language="en", clean=False, char_span=True)
    raw_spans = seg.segment(text)
    spans = cast(tuple[TextSpan, ...], raw_spans)

    assert len(spans) == 2
    assert spans[0].sent.strip().startswith("One further habit")
    assert spans[1].sent.strip().startswith(". . . The practice")
    # Verify no PUA sentinels leak into sentence strings
    for span in spans:
        assert not any(ord(c) >= 0xE000 and ord(c) <= 0xF8FF for c in span.sent)


def test_exception_with_doc_type_pdf_and_clean_false() -> None:
    """Verify ValueError when doc_type is pdf but clean is False."""
    with pytest.raises(ValueError) as excinfo:
        _ = csbd.Segmenter(language="en", clean=False, doc_type="pdf")
    assert "`doc_type='pdf'` requires `clean=True`" in str(excinfo.value)


@pytest.mark.parametrize("text, expected", PDF_CASES)
def test_pdf_segmentation(text: str, expected: tuple[str, ...]) -> None:
    """Verify sentence boundary segmentation on PDF documents."""
    seg = csbd.Segmenter(language="en", clean=True, doc_type="pdf")
    raw_segments = seg.segment(text)
    segments = cast(list[str], raw_segments)
    stripped: list[str] = [s.strip() for s in segments]
    assert stripped == list(expected)


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
    segmenter = csbd.Segmenter(language="en", clean=True, char_span=False)
    raw_segments = segmenter.segment(text)
    sentences = cast(list[str], raw_segments)

    output_lines: list[str] = [
        f"=== cleave-sbd Segmentation Output ({len(sentences)} Sentences) ===",
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
    assert "=== cleave-sbd Segmentation Output" in content


def test_segmenter_stream() -> None:
    """Verify streaming generator yields identical sentences across paragraph chunks."""
    text = (
        "Hello world! This is paragraph one.\n\n"
        "Here begins paragraph two. It has two sentences.\n\n"
        "Paragraph three is here. It is great."
    )
    segmenter = csbd.Segmenter(language="en", clean=False, char_span=False)
    streamed = list(segmenter.stream(text, chunk_paragraphs=1))
    batched = list(segmenter.segment(text))
    assert streamed == batched

    # Test chunk_paragraphs > 1
    streamed_multi = list(segmenter.stream(text, chunk_paragraphs=2))
    assert streamed_multi == batched

    # Test char_span streaming with exact batch-stream parity
    span_segmenter = csbd.Segmenter(language="en", clean=False, char_span=True)
    streamed_spans = list(span_segmenter.stream(text, chunk_paragraphs=1))
    batched_spans = list(span_segmenter.segment(text))
    assert streamed_spans == batched_spans

    # Verify trailing delimiter metadata on intermediate chunks
    assert cast(TextSpan, streamed_spans[1]).trailing_delim == "\n\n"
    assert cast(TextSpan, streamed_spans[3]).trailing_delim == "\n\n"
    assert cast(TextSpan, streamed_spans[-1]).trailing_delim == ""
