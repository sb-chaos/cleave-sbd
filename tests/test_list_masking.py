"""Unit tests for the list item masking and length preservation invariants."""

from __future__ import annotations

import pytest

from fracture.disambiguator import mask_list_items
from fracture.rules import (
    PUA_LEFT_PAREN,
    PUA_PERIOD,
    PUA_RIGHT_PAREN,
    unmask_all,
)
from tests.loaders import load_list_item_cases

LIST_ITEM_CASES, LIST_ITEM_INVARIANTS = load_list_item_cases()


@pytest.mark.parametrize(
    "description, input_text, expected_unmasked, expect_pua_period, expect_pua_parens",
    LIST_ITEM_CASES,
    ids=[c.description for c in LIST_ITEM_CASES],
)
def test_list_item_masking_cases(
    description: str,
    input_text: str,
    expected_unmasked: str,
    expect_pua_period: bool,
    expect_pua_parens: bool,
) -> None:
    """Verify list item masking engine behavior against TOML test cases."""
    masked = mask_list_items(input_text)
    assert len(masked) == len(input_text)
    if expect_pua_period:
        assert PUA_PERIOD in masked
    if expect_pua_parens:
        assert (PUA_LEFT_PAREN in masked) or (PUA_RIGHT_PAREN in masked)
    assert unmask_all(masked) == expected_unmasked


@pytest.mark.parametrize("sample", LIST_ITEM_INVARIANTS)
def test_list_item_masking_length_invariance(sample: str) -> None:
    """Verify length preservation invariant for list item masking."""
    masked = mask_list_items(sample)
    assert len(masked) == len(sample), f"Length mismatch for {sample!r}"

