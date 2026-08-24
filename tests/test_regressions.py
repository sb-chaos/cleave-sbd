"""GitHub issue regression test suites."""

from __future__ import annotations

from typing import cast

import pytest

import csbd
from csbd.segmenter import TextSpan
from tests.loaders import load_issues_cases

ISSUE_CASES, ISSUE_CHAR_SPAN_CASES = load_issues_cases()


@pytest.mark.parametrize(
    "issue, text, expected",
    ISSUE_CASES,
    ids=[f"{c.issue}_{idx}" for idx, c in enumerate(ISSUE_CASES)],
)
def test_issue_regression(issue: str, text: str, expected: tuple[str, ...]) -> None:
    """Verify bugfix regressions reported in GitHub issues."""
    seg = csbd.Segmenter(language="en", clean=False)
    raw_segments = seg.segment(text)
    segments = cast(list[str], raw_segments)
    stripped: list[str] = [s.strip() for s in segments]
    assert stripped == list(expected)
    assert text == " ".join(stripped)


@pytest.mark.parametrize(
    "issue, text, expected",
    ISSUE_CHAR_SPAN_CASES,
    ids=[f"{c.issue}_span_{idx}" for idx, c in enumerate(ISSUE_CHAR_SPAN_CASES)],
)
def test_issue_char_spans(
    issue: str,
    text: str,
    expected: tuple[tuple[str, int, int], ...],
) -> None:
    """Verify character offset span tracking across issue regression cases."""
    seg = csbd.Segmenter(language="en", clean=False, char_span=True)
    raw_segments = seg.segment(text)
    segments = cast(list[TextSpan], raw_segments)
    expected_text_spans = [
        TextSpan(sent=span[0], start=span[1], end=span[2]) for span in expected
    ]
    assert tuple(segments) == tuple(expected_text_spans)
    assert text == "".join(s.sent for s in segments)


def test_zero_runtime_dependencies_invariant() -> None:
    """Enforce the strict architectural invariant: zero external runtime dependencies."""
    import tomllib
    from pathlib import Path

    pyproject_path = Path(__file__).resolve().parent.parent / "pyproject.toml"
    with open(pyproject_path, "rb") as f:
        data = tomllib.load(f)

    dependencies = data.get("project", {}).get("dependencies", None)
    assert dependencies == [], (
        f"CRITICAL INVARIANT VIOLATION: cleave-sbd must have ZERO runtime dependencies! "
        f"Found unexpected dependencies: {dependencies}"
    )
