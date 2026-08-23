"""Normalizer cleaning patterns, whitespace rules, HTML strippers, and PDF fixers."""

from __future__ import annotations

import re

from fracture.rules.disambiguation import Rule

URL_EMAIL_KEYWORDS: tuple[str, ...] = (
    ".com",
    ".net",
    ".org",
    ".io",
    ".gov",
    ".edu",
    "http://",
    "https://",
    "@",
    "www.",
)

# Text & Whitespace Normalization Rules
NL_IN_WORD: Rule = Rule(re.compile(r"\n(?=[a-zA-Z]{1,2}\n)"))
DOUBLE_NL_SPACE: Rule = Rule(re.compile(r"\n \n"), "\r")
DOUBLE_NL: Rule = Rule(re.compile(r"\n\n"), "\r")
NL_BEFORE_PERIOD: Rule = Rule(re.compile(r"\n(?=\.(\s|\n))"))
NL_TO_CR: Rule = Rule(re.compile(r"\n"), "\r")
ESCAPED_NL: Rule = Rule(re.compile(r"\\n"), "\n")
ESCAPED_CR: Rule = Rule(re.compile(r"\\r"), "\r")
TYPO_ESCAPED_NL: Rule = Rule(re.compile(r"\\\ n"), "\n")
TYPO_ESCAPED_CR: Rule = Rule(re.compile(r"\\\ r"), "\r")
INLINE_FORMATTING: Rule = Rule(re.compile(r"{b\^&gt;\d*&lt;b\^}|{b\^>\d*<b\^}"))
TABLE_OF_CONTENTS: Rule = Rule(re.compile(r"\.{4,}\s*\d+-*\d*"), "\r")
CONSECUTIVE_PERIODS: Rule = Rule(re.compile(r"\.{5,}"), " ")
CONSECUTIVE_SLASHES: Rule = Rule(re.compile(r"/{3}"))
NO_SPACE_SENTENCE_COMBINED: re.Pattern[str] = re.compile(r"(?<=[a-z\d])\.(?=[A-Z])")
NL_IN_SENTENCE: Rule = Rule(re.compile(r"(?<=\s)\n(?=([a-z]|\())"))
NL_BEFORE_BULLET: Rule = Rule(re.compile(r"\n(?=•)"), "\r")
NORMAL_QUOTES: Rule = Rule(re.compile(r"''|``"), '"')

# HTML Rules
HTML_TAG_RULE: Rule = Rule(
    re.compile(r"<\/?\w+((\s+\w+(\s*=\s*(?:\".*?\"|'.*?'|[\^'\">\s]+))?)+\s*|\s*)\/?>")
)
HTML_ESCAPED_TAG_RULE: Rule = Rule(re.compile(r"&lt;\/?[^gt;]*gt;"))
HTML_RULES: tuple[Rule, ...] = (HTML_TAG_RULE, HTML_ESCAPED_TAG_RULE)

# PDF Rules
PDF_NEW_LINE_MID_SENTENCE: Rule = Rule(re.compile(r"(?<=[^\n]\s)\n(?=\S)"))
PDF_NEW_LINE_MID_SENTENCE_NOSPACE: Rule = Rule(re.compile(r"\n(?=[a-z])"), " ")


def replace_no_space_sentence(match: re.Match[str]) -> str:
    """Insert period-space after sentences lacking whitespace, protecting URLs/emails."""
    start = match.start()
    text = match.string

    word_start = start
    while word_start > 0 and text[word_start - 1] not in " \n\r\t":
        word_start -= 1

    word_end = start + 1
    text_len = len(text)
    while word_end < text_len and text[word_end] not in " \n\r\t":
        word_end += 1

    word = text[word_start:word_end].lower()
    if any(keyword in word for keyword in URL_EMAIL_KEYWORDS):
        return match.group(0)
    return ". "
