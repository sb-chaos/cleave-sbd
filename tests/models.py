"""Strongly-typed frozen dataclasses for test inputs and expected outputs."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class SbdTestCase:
    """Strongly-typed sentence boundary disambiguation test case."""

    text: str
    expected: tuple[str, ...]
    language: str
    clean: bool
    doc_type: str = ""
    xfail: bool = False
    suite: str = "default"


@dataclass(frozen=True, slots=True)
class IssueTestCase:
    """Strongly-typed GitHub issue regression test case."""

    issue: str
    text: str
    expected: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class IssueCharSpanTestCase:
    """Strongly-typed character span regression test case."""

    issue: str
    text: str
    expected: tuple[tuple[str, int, int], ...]


@dataclass(frozen=True, slots=True)
class NormalizerTestCase:
    """Strongly-typed text normalizer test case."""

    text: str
    expected: str


@dataclass(frozen=True, slots=True)
class ListItemMaskTestCase:
    """Strongly-typed list item masking test case."""

    description: str
    input: str
    expected_unmasked: str
    expect_pua_period: bool
    expect_pua_parens: bool


@dataclass(frozen=True, slots=True)
class PdfTestCase:
    """Strongly-typed PDF document segmentation test case."""

    text: str
    expected: tuple[str, ...]
