import pytest
from pragmatic_sbd.lang import LANGUAGE_CODES, Language


def test_lang_code2instance_mapping():
    for code, language_module in LANGUAGE_CODES.items():
        assert Language.get_language_code(code) == language_module


def test_exception_on_no_lang_code_provided():
    with pytest.raises(ValueError) as e:
        Language.get_language_code("")
    assert "Provide valid language ID i.e. ISO code." in str(e.value)


def test_exception_on_unsupported_lang_code_provided():
    with pytest.raises(ValueError) as e:
        Language.get_language_code("elvish")
    assert "Provide valid language ID i.e. ISO code." in str(e.value)


def test_toml_configs_validity():
    from pragmatic_sbd.lang import SUPPORTED_LANGUAGES, LanguageConfig
    import re

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
