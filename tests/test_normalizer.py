"""Unit tests for text normalization and cleaner pipeline."""

from __future__ import annotations

from typing import Final

import pytest

from fracture.lang import Language
from fracture.normalizer import Normalizer
from tests.loaders import load_normalizer_cases
from tests.models import NormalizerTestCase

NORMALIZER_CASES: Final[list[NormalizerTestCase]] = load_normalizer_cases()


@pytest.mark.parametrize("case", NORMALIZER_CASES)
def test_normalizer_cases(case: NormalizerTestCase) -> None:
    """Verify text normalization from TOML test cases."""
    norm_text = Normalizer(case.text, Language.get_language_code("en")).normalize()
    assert norm_text == case.expected


def test_normalizer_immutability() -> None:
    """Verify normalizer does not mutate input text."""
    text = "It was a cold \nnight in the city."
    _ = Normalizer(text, Language.get_language_code("en")).normalize()
    assert text == "It was a cold \nnight in the city."


@pytest.mark.parametrize("empty_val", [None, ""])
def test_normalizer_empty_and_none_inputs(empty_val: str | None) -> None:
    """Verify normalizer handling of empty and None input values."""
    cleaned = Normalizer(empty_val, Language.get_language_code("en")).normalize()
    assert cleaned == empty_val
