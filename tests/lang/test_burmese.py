# -*- coding: utf-8 -*-
import pytest

<<<<<<< HEAD
GOLDEN_MY_RULES_TEST_CASES = [("ခင္ဗ်ားနာမည္ဘယ္လိုေခၚလဲ။၇ွင္ေနေကာင္းလား။", ["ခင္ဗ်ားနာမည္ဘယ္လိုေခၚလဲ။", "၇ွင္ေနေကာင္းလား။"])]


@pytest.mark.parametrize("text,expected_sents", GOLDEN_MY_RULES_TEST_CASES)
=======
GOLDEN_MY_RULES_TEST_CASES = [
("ခင္ဗ်ားနာမည္ဘယ္လိုေခၚလဲ။၇ွင္ေနေကာင္းလား။",
 ["ခင္ဗ်ားနာမည္ဘယ္လိုေခၚလဲ။", "၇ွင္ေနေကာင္းလား။"])
]

@pytest.mark.parametrize('text,expected_sents', GOLDEN_MY_RULES_TEST_CASES)
>>>>>>> add-type-annotations
def test_my_sbd(my_default_fixture, text, expected_sents):
    """Burmese language SBD tests"""
    segments = my_default_fixture.segment(text)
    segments = [s.strip() for s in segments]
    assert segments == expected_sents
