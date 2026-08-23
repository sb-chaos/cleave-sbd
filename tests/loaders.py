"""Data loader and deserialization helpers for externalized TOML test suites."""

from __future__ import annotations

import tomllib
from pathlib import Path
from typing import Any, Final

from tests.models import (
    IssueCharSpanTestCase,
    IssueTestCase,
    ListItemMaskTestCase,
    NormalizerTestCase,
    PdfTestCase,
    SbdTestCase,
)

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


def load_all_language_sbd_cases() -> list[SbdTestCase]:
    """Ingest and validate all language-specific test cases from TOML files."""
    cases: list[SbdTestCase] = []
    lang_dir = DATA_DIR / "lang"

    for toml_path in sorted(lang_dir.glob("*.toml")):
        lang_name = toml_path.stem
        iso_code = LANG_NAME_TO_CODE[lang_name]

        with open(toml_path, "rb") as f:
            data: dict[str, list[dict[str, Any]]] = tomllib.load(f)

        for section_name, items in data.items():
            is_clean = ("clean" in section_name) and ("wo_clean" not in section_name)
            is_pdf = "pdf" in section_name
            doc_type: str = "pdf" if is_pdf else ""
            if is_pdf:
                is_clean = True

            for item in items:
                text_val: str = item["text"]
                expected_val: tuple[str, ...] = tuple(item["expected"])
                xfail_val: bool = bool(item.get("xfail", False))

                cases.append(
                    SbdTestCase(
                        text=text_val,
                        expected=expected_val,
                        language=iso_code,
                        clean=is_clean,
                        doc_type=doc_type,
                        xfail=xfail_val,
                        suite=f"{lang_name}:{section_name}",
                    )
                )

    return cases


def load_issues_cases() -> tuple[list[IssueTestCase], list[IssueCharSpanTestCase]]:
    """Ingest and validate issue regression test cases from TOML."""
    with open(DATA_DIR / "issues.toml", "rb") as f:
        data: dict[str, list[dict[str, Any]]] = tomllib.load(f)

    issue_cases: list[IssueTestCase] = [
        IssueTestCase(
            issue=item["issue"],
            text=item["text"],
            expected=tuple(item["expected"]),
        )
        for item in data.get("cases", [])
    ]

    char_span_cases: list[IssueCharSpanTestCase] = [
        IssueCharSpanTestCase(
            issue=item["issue"],
            text=item["text"],
            expected=tuple(
                (span[0], int(span[1]), int(span[2])) for span in item["expected"]
            ),
        )
        for item in data.get("char_span_cases", [])
    ]

    return issue_cases, char_span_cases


def load_normalizer_cases() -> list[NormalizerTestCase]:
    """Ingest normalizer test cases from TOML."""
    with open(DATA_DIR / "normalizer.toml", "rb") as f:
        data: dict[str, list[dict[str, Any]]] = tomllib.load(f)

    return [
        NormalizerTestCase(text=item["text"], expected=item["expected"])
        for item in data.get("cases", [])
    ]


def load_list_item_cases() -> tuple[list[ListItemMaskTestCase], list[str]]:
    """Ingest list item mask test cases and invariants from TOML."""
    with open(DATA_DIR / "list_items.toml", "rb") as f:
        data: dict[str, Any] = tomllib.load(f)

    cases = [
        ListItemMaskTestCase(
            description=item["description"],
            input=item["input"],
            expected_unmasked=item["expected_unmasked"],
            expect_pua_period=bool(item["expect_pua_period"]),
            expect_pua_parens=bool(item["expect_pua_parens"]),
        )
        for item in data.get("cases", [])
    ]
    invariants: list[str] = list(
        data.get("invariants", {}).get("length_preserving_samples", [])
    )
    return cases, invariants


def load_pdf_cases() -> list[PdfTestCase]:
    """Ingest PDF segmentation test cases from TOML."""
    with open(DATA_DIR / "pdf.toml", "rb") as f:
        data: dict[str, list[dict[str, Any]]] = tomllib.load(f)

    return [
        PdfTestCase(text=item["text"], expected=tuple(item["expected"]))
        for item in data.get("cases", [])
    ]
