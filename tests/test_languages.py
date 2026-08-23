"""Language SBD execution and dynamic configuration validation tests."""

from __future__ import annotations

import re
from typing import Final, cast

import pytest

import fracture
from fracture.lang import SUPPORTED_LANGUAGES, Language, LanguageConfig
from tests.loaders import load_all_language_sbd_cases
from tests.models import SbdTestCase

ALL_SBD_CASES: Final[list[SbdTestCase]] = load_all_language_sbd_cases()


@pytest.mark.parametrize(
    "case",
    [
        pytest.param(
            case,
            id=f"{case.language}_{case.suite}_{idx}",
            marks=pytest.mark.xfail if case.xfail else (),
        )
        for idx, case in enumerate(ALL_SBD_CASES)
    ],
)
def test_language_sentence_boundary_disambiguation(case: SbdTestCase) -> None:
    """Execute sentence boundary disambiguation for a typed language test case."""
    segmenter = fracture.Segmenter(
        language=case.language,
        clean=case.clean,
        doc_type=case.doc_type,
    )
    raw_segments = segmenter.segment(case.text)
    segments = cast(list[str], raw_segments)
    stripped_segments: list[str] = [s.strip() for s in segments]
    assert stripped_segments == list(case.expected)


def test_lang_code2instance_mapping() -> None:
    """Verify all ISO language codes map to their corresponding LanguageConfig."""
    for code in SUPPORTED_LANGUAGES:
        config = Language.get_language_code(code)
        assert isinstance(config, LanguageConfig)
        assert config.iso_code == code


@pytest.mark.parametrize("invalid_code", ["", "elvish", "123"])
def test_exception_on_invalid_lang_code(invalid_code: str) -> None:
    """Verify ValueError is raised when providing invalid language codes."""
    with pytest.raises(ValueError) as excinfo:
        Language.get_language_code(invalid_code)
    assert "Provide valid language ID i.e. ISO code." in str(excinfo.value)


def test_toml_configs_validity() -> None:
    """Verify structure and type integrity of all language configuration files."""
    for code in SUPPORTED_LANGUAGES:
        config = Language.get_language_code(code)
        assert isinstance(config, LanguageConfig)
        assert config.iso_code == code
        assert isinstance(config.abbreviations, frozenset)
        assert isinstance(config.prepositive_abbreviations, frozenset)
        assert isinstance(config.number_abbreviations, frozenset)
        assert isinstance(config.sentence_starters, frozenset)
        assert config.punctuations is None or isinstance(config.punctuations, frozenset)
        assert config.sentence_boundary_regex is None or isinstance(
            config.sentence_boundary_regex, re.Pattern
        )
        assert config.multi_period_abbreviation_regex is None or isinstance(
            config.multi_period_abbreviation_regex, re.Pattern
        )
        assert isinstance(config.rules, tuple)
        for r in config.rules:
            assert isinstance(r.pattern, re.Pattern)
            assert isinstance(r.replacement, str)
        assert isinstance(config.clean_rules, tuple)
        for r in config.clean_rules:
            assert isinstance(r.pattern, re.Pattern)
            assert isinstance(r.replacement, str)
        assert isinstance(config.paired_punctuation_patterns, tuple)
        for p in config.paired_punctuation_patterns:
            assert isinstance(p, re.Pattern)
