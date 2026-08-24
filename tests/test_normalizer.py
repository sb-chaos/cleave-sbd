"""Unit tests for text normalization and cleaner pipeline."""

from __future__ import annotations

from typing import Final

import pytest

from csbd.language import Language
from csbd.normalizer import normalize
from tests.loaders import NormalizerCase, load_normalizer_cases

NORMALIZER_CASES: Final[list[NormalizerCase]] = load_normalizer_cases()


@pytest.mark.parametrize("text, expected", NORMALIZER_CASES)
def test_normalizer_cases(text: str, expected: str) -> None:
    """Verify text normalization from TOML test cases."""
    norm_text = normalize(text, config=Language.get_language_code("en"))
    assert norm_text == expected


def test_normalizer_immutability() -> None:
    """Verify normalizer does not mutate input text."""
    text = "It was a cold \nnight in the city."
    _ = normalize(text, config=Language.get_language_code("en"))
    assert text == "It was a cold \nnight in the city."


@pytest.mark.parametrize("empty_val", [None, ""])
def test_normalizer_empty_and_none_inputs(empty_val: str | None) -> None:
    """Verify normalizer handling of empty and None input values."""
    cleaned = normalize(empty_val, config=Language.get_language_code("en"))
    assert cleaned == empty_val
