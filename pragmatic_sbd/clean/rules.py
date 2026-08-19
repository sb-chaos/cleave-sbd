"""Text normalization and document-cleaning regex rules."""

import re

from pragmatic_sbd.lang.common import Rule

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
NL_IN_WORD = Rule(re.compile(r"\n(?=[a-zA-Z]{1,2}\n)"))
DOUBLE_NL_SPACE = Rule(re.compile(r"\n \n"), "\r")
DOUBLE_NL = Rule(re.compile(r"\n\n"), "\r")
NL_BEFORE_PERIOD = Rule(re.compile(r"\n(?=\.(\s|\n))"))
NL_TO_CR = Rule(re.compile(r"\n"), "\r")
ESCAPED_NL = Rule(re.compile(r"\\n"), "\n")
ESCAPED_CR = Rule(re.compile(r"\\r"), "\r")
TYPO_ESCAPED_NL = Rule(re.compile(r"\\\ n"), "\n")
TYPO_ESCAPED_CR = Rule(re.compile(r"\\\ r"), "\r")
INLINE_FORMATTING = Rule(re.compile(r"{b\^&gt;\d*&lt;b\^}|{b\^>\d*<b\^}"))
TABLE_OF_CONTENTS = Rule(re.compile(r"\.{4,}\s*\d+-*\d*"), "\r")
CONSECUTIVE_PERIODS = Rule(re.compile(r"\.{5,}"), " ")
CONSECUTIVE_SLASHES = Rule(re.compile(r"/{3}"))
NO_SPACE_SENTENCE_ALPHA = Rule(re.compile(r"(?<=[a-z])\.(?=[A-Z])"), ". ")
NO_SPACE_SENTENCE_DIGIT = Rule(re.compile(r"(?<=\d)\.(?=[A-Z])"), ". ")
NL_IN_SENTENCE = Rule(re.compile(r"(?<=\s)\n(?=([a-z]|\())"))
NL_BEFORE_BULLET = Rule(re.compile(r"\n(?=•)"), "\r")
NORMAL_QUOTES = Rule(re.compile(r"''|``"), '"')

# HTML Rules
HTML_TAG_RULE = Rule(re.compile(r"<\/?\w+((\s+\w+(\s*=\s*(?:\".*?\"|'.*?'|[\^'\">\s]+))?)+\s*|\s*)\/?>"))
HTML_ESCAPED_TAG_RULE = Rule(re.compile(r"&lt;\/?[^gt;]*gt;"))
HTML_RULES: tuple[Rule, ...] = (HTML_TAG_RULE, HTML_ESCAPED_TAG_RULE)

# PDF Rules
PDF_NEW_LINE_MID_SENTENCE = Rule(re.compile(r"(?<=[^\n]\s)\n(?=\S)"))
PDF_NEW_LINE_MID_SENTENCE_NOSPACE = Rule(re.compile(r"\n(?=[a-z])"), " ")
