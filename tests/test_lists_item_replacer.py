"""Unit tests for the refactored list item masking engine."""

import pytest
<<<<<<< HEAD
from pragmatic_sbd.lang.common import (
=======
from pragmatic_sbd.lang.common.standard import (
>>>>>>> add-type-annotations
    PUA_LEFT_PAREN,
    PUA_PERIOD,
    PUA_RIGHT_PAREN,
    unmask_all,
)
<<<<<<< HEAD
from pragmatic_sbd.disambiguator import mask_list_items
=======
from pragmatic_sbd.lists_item_replacer import ListItemReplacer, mask_list_items
>>>>>>> add-type-annotations


class TestListItemMasking:
    """Test suite for mask_list_items and ListItemReplacer."""

    def test_empty_string(self) -> None:
        assert mask_list_items("") == ""

    def test_numbered_list_with_periods(self) -> None:
        text = "1. First item 2. Second item 3. Third item"
        masked = mask_list_items(text)
        assert len(masked) == len(text)
        assert PUA_PERIOD in masked
        assert "\r" in masked
        assert unmask_all(masked) == "1. First item\r2. Second item\r3. Third item"

    def test_numbered_list_with_parens(self) -> None:
        text = "1) First item 2) Second item 3) Third item"
        masked = mask_list_items(text)
        assert len(masked) == len(text)
        assert "\r" in masked
        assert unmask_all(masked) == "1) First item\r2) Second item\r3) Third item"

    def test_numbered_list_with_period_and_parens(self) -> None:
        text = "1.) First item 2.) Second item"
        masked = mask_list_items(text)
        assert len(masked) == len(text)
        assert PUA_PERIOD in masked
        assert "\r" in masked

    def test_parenthesized_numbered_list(self) -> None:
        text = "(1) First item (2) Second item"
        masked = mask_list_items(text)
        assert len(masked) == len(text)
        assert PUA_LEFT_PAREN in masked
        assert PUA_RIGHT_PAREN in masked
        assert "\r" in masked
        assert unmask_all(masked) == "(1) First item\r(2) Second item"

    def test_bulleted_numbered_list(self) -> None:
        text = "• 9. The first item • 10. The second item"
        masked = mask_list_items(text)
        assert len(masked) == len(text)
        assert PUA_PERIOD in masked
        assert "\r" in masked

    def test_hyphen_numbered_list(self) -> None:
        text = "⁃9. The first item ⁃10. The second item"
        masked = mask_list_items(text)
        assert len(masked) == len(text)
        assert PUA_PERIOD in masked
        assert "\r" in masked

    def test_alphabetical_list_with_periods(self) -> None:
        text = "a. The first item b. The second item c. The third list item"
        masked = mask_list_items(text)
        assert len(masked) == len(text)
        assert PUA_PERIOD in masked
        assert "\r" in masked
        assert unmask_all(masked) == "a. The first item\rb. The second item\rc. The third list item"

    def test_alphabetical_list_with_parens(self) -> None:
        text = "a) The first item b) The second item c) The third list item"
        masked = mask_list_items(text)
        assert len(masked) == len(text)
        assert "\r" in masked

    def test_roman_numeral_list_in_parens(self) -> None:
        text = "(i) Hello world. (ii) Hello world. (iii) Hello world."
        masked = mask_list_items(text)
        assert len(masked) == len(text)
        assert PUA_LEFT_PAREN in masked
        assert PUA_RIGHT_PAREN in masked
        assert unmask_all(masked) == "(i) Hello world.\r(ii) Hello world.\r(iii) Hello world."

    def test_single_roman_numeral_item(self) -> None:
        text = "(iii) List item number 3."
        masked = mask_list_items(text)
        assert len(masked) == len(text)
        assert PUA_LEFT_PAREN in masked
        assert PUA_RIGHT_PAREN in masked
        assert unmask_all(masked) == text

    def test_length_preserving_invariant(self) -> None:
        samples = [
            "1. Item 1 2. Item 2 3. Item 3",
            "1) Item 1 2) Item 2",
            "(1) Item 1 (2) Item 2",
            "a. First b. Second c. Third",
            "(i) First (ii) Second (iii) Third",
            "• 9. First • 10. Second",
            "⁃9. First ⁃10. Second",
            "This is normal text without lists.",
            "She has $100.00 in her bag.",
            "In section III, (9) will be used.",
        ]
        for s in samples:
            masked = mask_list_items(s)
            assert len(masked) == len(s), f"Length mismatch for {s!r}: {len(masked)} != {len(s)}"
<<<<<<< HEAD
=======

    def test_legacy_class_interface(self) -> None:
        replacer = ListItemReplacer("1. Item 1 2. Item 2")
        result = replacer.add_line_break()
        assert len(result) == len("1. Item 1 2. Item 2")
        assert replacer.ROMAN_NUMERALS
        assert replacer.LATIN_NUMERALS
>>>>>>> add-type-annotations
