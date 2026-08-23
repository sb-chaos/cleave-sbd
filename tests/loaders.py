"""Data loader and deserialization helpers for externalized TOML test suites.

Uses lightweight NamedTuples to ensure zero dict-allocation overhead, strict typing,
and clean tuple-unpacking in pytest parametrizations.
"""

from __future__ import annotations

import tomllib
from pathlib import Path
from typing import Any, Final, NamedTuple, cast

DATA_DIR: Final[Path] = Path(__file__).parent / "data"

LANG_NAME_TO_CODE: Final[dict[str, str]] = {
    "amharic": "am",
    "arabic": "ar",
    "armenian": "hy",
    "bulgarian": "bg",
    "burmese": "my",
    "chinese": "zh",
    "danish": "da",
    "deutsch": "de",
    "dutch": "nl",
    "english": "en",
    "english_clean": "en",
    "french": "fr",
    "greek": "el",
    "hindi": "hi",
    "italian": "it",
    "japanese": "ja",
    "kazakh": "kk",
    "marathi": "mr",
    "persian": "fa",
    "polish": "pl",
    "russian": "ru",
    "slovak": "sk",
    "spanish": "es",
    "urdu": "ur",
}


# -----------------------------------------------------------------------------
# Lightweight NamedTuples (Memory-Efficient C-Tuples)
# -----------------------------------------------------------------------------


class SbdCase(NamedTuple):
    """Sentence boundary disambiguation test case tuple."""

    text: str
    expected: tuple[str, ...]
    language: str
    clean: bool
    doc_type: str = ""


class IssueCase(NamedTuple):
    """GitHub issue regression test case tuple."""

    issue: str
    text: str
    expected: tuple[str, ...]


class IssueCharSpanCase(NamedTuple):
    """Character offset span regression test case tuple."""

    issue: str
    text: str
    expected: tuple[tuple[str, int, int], ...]


class NormalizerCase(NamedTuple):
    """Text normalization test case tuple."""

    text: str
    expected: str


class ListItemMaskCase(NamedTuple):
    """List item masking test case tuple."""

    description: str
    input: str
    expected_unmasked: str
    expect_pua_period: bool
    expect_pua_parens: bool


class PdfCase(NamedTuple):
    """PDF document segmentation test case tuple."""

    text: str
    expected: tuple[str, ...]


# -----------------------------------------------------------------------------
# TOML Data Ingestion Helpers
# -----------------------------------------------------------------------------


def load_language_sbd_cases() -> list[SbdCase]:
    """Ingest language test cases from TOML and return typed SbdCase namedtuples."""
    sbd_cases: list[SbdCase] = []
    language_directory: Path = DATA_DIR / "lang"

    for toml_path in sorted(language_directory.glob("*.toml")):
        language_name: str = toml_path.stem
        iso_language_code: str = LANG_NAME_TO_CODE[language_name]

        with open(toml_path, "rb") as toml_file:
            toml_data: dict[str, Any] = tomllib.load(toml_file)

        for section_name, test_records in toml_data.items():
            is_clean_enabled: bool = ("clean" in section_name) and (
                "wo_clean" not in section_name
            )
            is_pdf_document: bool = "pdf" in section_name
            document_type: str = "pdf" if is_pdf_document else ""
            if is_pdf_document:
                is_clean_enabled = True

            records_list = cast(list[dict[str, Any]], test_records)
            for record in records_list:
                input_text: str = str(record["text"])
                expected_list = cast(list[Any], record["expected"])
                expected_sentences: tuple[str, ...] = tuple(
                    str(sentence) for sentence in expected_list
                )
                case = SbdCase(
                    text=input_text,
                    expected=expected_sentences,
                    language=iso_language_code,
                    clean=is_clean_enabled,
                    doc_type=document_type,
                )
                sbd_cases.append(case)

    return sbd_cases


def load_language_sbd_cases_with_metadata() -> list[tuple[SbdCase, str, bool]]:
    """Ingest language test cases from TOML returning (case, case_identifier, is_xfail)."""
    cases_with_metadata: list[tuple[SbdCase, str, bool]] = []
    language_directory: Path = DATA_DIR / "lang"

    for toml_path in sorted(language_directory.glob("*.toml")):
        language_name: str = toml_path.stem
        iso_language_code: str = LANG_NAME_TO_CODE[language_name]

        with open(toml_path, "rb") as toml_file:
            toml_data: dict[str, Any] = tomllib.load(toml_file)

        for section_name, test_records in toml_data.items():
            is_clean_enabled: bool = ("clean" in section_name) and (
                "wo_clean" not in section_name
            )
            is_pdf_document: bool = "pdf" in section_name
            document_type: str = "pdf" if is_pdf_document else ""
            if is_pdf_document:
                is_clean_enabled = True

            records_list = cast(list[dict[str, Any]], test_records)
            for record_index, record in enumerate(records_list):
                input_text: str = str(record["text"])
                expected_list = cast(list[Any], record["expected"])
                expected_sentences: tuple[str, ...] = tuple(
                    str(sentence) for sentence in expected_list
                )
                case = SbdCase(
                    text=input_text,
                    expected=expected_sentences,
                    language=iso_language_code,
                    clean=is_clean_enabled,
                    doc_type=document_type,
                )
                case_identifier: str = (
                    f"{iso_language_code}_{language_name}:{section_name}_{record_index}"
                )
                is_xfail: bool = bool(record.get("xfail", False))
                cases_with_metadata.append((case, case_identifier, is_xfail))

    return cases_with_metadata


def load_issues_cases() -> tuple[list[IssueCase], list[IssueCharSpanCase]]:
    """Ingest issue regression test cases from TOML."""
    with open(DATA_DIR / "issues.toml", "rb") as toml_file:
        toml_data: dict[str, Any] = tomllib.load(toml_file)

    issue_cases: list[IssueCase] = []
    cases_list = cast(list[dict[str, Any]], toml_data.get("cases", []))
    for record in cases_list:
        input_text: str = str(record["text"])
        expected_list = cast(list[Any], record["expected"])
        expected_sentences: tuple[str, ...] = tuple(
            str(sentence) for sentence in expected_list
        )
        issue_cases.append(
            IssueCase(
                issue=str(record["issue"]),
                text=input_text,
                expected=expected_sentences,
            )
        )

    char_span_cases: list[IssueCharSpanCase] = []
    char_spans_list = cast(list[dict[str, Any]], toml_data.get("char_span_cases", []))
    for record in char_spans_list:
        raw_spans = cast(list[list[Any]], record["expected"])
        parsed_spans: list[tuple[str, int, int]] = [
            (str(span[0]), int(span[1]), int(span[2])) for span in raw_spans
        ]
        char_span_cases.append(
            IssueCharSpanCase(
                issue=str(record["issue"]),
                text=str(record["text"]),
                expected=tuple(parsed_spans),
            )
        )

    return issue_cases, char_span_cases


def load_normalizer_cases() -> list[NormalizerCase]:
    """Ingest normalizer test cases from TOML."""
    with open(DATA_DIR / "normalizer.toml", "rb") as toml_file:
        toml_data: dict[str, Any] = tomllib.load(toml_file)

    normalizer_cases: list[NormalizerCase] = []
    cases_list = cast(list[dict[str, Any]], toml_data.get("cases", []))
    for record in cases_list:
        input_text: str = str(record["text"])
        expected_text: str = str(record["expected"])
        normalizer_cases.append(NormalizerCase(text=input_text, expected=expected_text))
    return normalizer_cases


def load_list_item_cases() -> tuple[list[ListItemMaskCase], list[str]]:
    """Ingest list item mask test cases and length-invariants from TOML."""
    with open(DATA_DIR / "list_items.toml", "rb") as toml_file:
        toml_data: dict[str, Any] = tomllib.load(toml_file)

    cases_list = cast(list[dict[str, Any]], toml_data.get("cases", []))
    mask_cases: list[ListItemMaskCase] = [
        ListItemMaskCase(
            description=str(record["description"]),
            input=str(record["input"]),
            expected_unmasked=str(record["expected_unmasked"]),
            expect_pua_period=bool(record["expect_pua_period"]),
            expect_pua_parens=bool(record["expect_pua_parens"]),
        )
        for record in cases_list
    ]

    invariants_dict = cast(dict[str, Any], toml_data.get("invariants", {}))
    raw_samples = cast(list[Any], invariants_dict.get("length_preserving_samples", []))
    length_invariants: list[str] = [str(sample) for sample in raw_samples]

    return mask_cases, length_invariants


def load_pdf_cases() -> list[PdfCase]:
    """Ingest PDF segmentation test cases from TOML."""
    with open(DATA_DIR / "pdf.toml", "rb") as toml_file:
        toml_data: dict[str, Any] = tomllib.load(toml_file)

    pdf_cases: list[PdfCase] = []
    cases_list = cast(list[dict[str, Any]], toml_data.get("cases", []))
    for record in cases_list:
        input_text: str = str(record["text"])
        expected_list = cast(list[Any], record["expected"])
        expected_sentences: tuple[str, ...] = tuple(
            str(sentence) for sentence in expected_list
        )
        pdf_cases.append(PdfCase(text=input_text, expected=expected_sentences))
    return pdf_cases
