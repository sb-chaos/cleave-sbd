"""File-based sentence segmentation test utility.

Reads arbitrary text from an input file, runs sentence boundary disambiguation,
and outputs numbered sentence sections to a target text file.
"""

from pathlib import Path

import pragmatic_sbd
from pragmatic_sbd import TextSpan

# Configurable file path strings
INPUT_FILE: str = "tests/sample_input.txt"
OUTPUT_FILE: str = "tests/sample_output.txt"


def segment_text_file(
    input_file_str: str = INPUT_FILE,
    output_file_str: str = OUTPUT_FILE,
    language: str = "en",
    clean: bool = True,
    char_span: bool = False,
) -> list[str]:
    """Read text from an input path, segment into sentences, and write numbered sections to output path.

    Parameters
    ----------
    input_file_str : str
        String path to input file containing arbitrary text.
    output_file_str : str
        String path to output file for formatted, numbered sentences.
    language : str
        ISO 639-1 language code (defaults to "en").
    clean : bool
        Whether to run text normalization cleaners.
    char_span : bool
        Whether to calculate character start/end offsets.

    Returns
    -------
    list[str]
        List of segmented sentence strings.
    """
    # Convert string paths to Path objects within the function
    input_path = Path(input_file_str)
    output_path = Path(output_file_str)

    # Ensure parent directories exist
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Create default sample input if missing
    if not input_path.exists():
        input_path.parent.mkdir(parents=True, exist_ok=True)
        default_sample = (
            "Hello world! This is the first test sentence. My name is Dr. Jonas E. Smith "
            "and I work in Washington, D.C. at 10.5% growth rate. Is this sentence number four?\n\n"
            "Here begins a new paragraph. Please refer to Fig. 1.2 on p. 45 for further details. "
            '"We will succeed!" said the director. The end.'
        )
        input_path.write_text(default_sample, encoding="utf-8")

    text = input_path.read_text(encoding="utf-8")

    segmenter = pragmatic_sbd.Segmenter(
        language=language,
        clean=clean,
        char_span=char_span,
    )
    raw_segments = segmenter.segment(text)

    output_lines: list[str] = [
        f"=== pragmatic_sbd Segmentation Output ({len(raw_segments)} Sentences) ===",
        f"Input File : {input_path.as_posix()}",
        f"Language   : {language}",
        f"Clean      : {clean}",
        f"Char Span  : {char_span}",
        "=" * 60,
        "",
    ]

    sentences: list[str] = []
    for index, item in enumerate(raw_segments, start=1):
        if isinstance(item, TextSpan):
            sentences.append(item.sent)
            output_lines.append(f"[{index}] Span: ({item.start}, {item.end})")
            output_lines.append(f"{item.sent}")
            output_lines.append("-" * 40)
        else:
            sentences.append(item)
            output_lines.append(f"[{index}]")
            output_lines.append(f"{item}")
            output_lines.append("-" * 40)

    output_content = "\n".join(output_lines) + "\n"
    output_path.write_text(output_content, encoding="utf-8")

    return sentences


def test_file_segmenter() -> None:
    """Verify file-based text segmentation and numbered output formatting."""
    sentences = segment_text_file(INPUT_FILE, OUTPUT_FILE)
    assert len(sentences) > 0

    out_path = Path(OUTPUT_FILE)
    assert out_path.exists()

    content = out_path.read_text(encoding="utf-8")
    assert "[1]" in content
    assert "=== pragmatic_sbd Segmentation Output" in content


if __name__ == "__main__":
    results = segment_text_file(INPUT_FILE, OUTPUT_FILE)
    print(f"Successfully segmented {len(results)} sentences.")
    print(f"Output saved to: {Path(OUTPUT_FILE).resolve()}")
