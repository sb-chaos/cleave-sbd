
# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2026-08-18

### Added
- Complete modern rewrite and architecture of the sentence boundary disambiguation engine.
- Declarative, pre-compiled regular expression pipeline replacing procedural loops.
- Pure functional, length-preserving Private Use Area (PUA) sentinel substitutions (`\ue000`–`\ue009`) guaranteeing $1:1$ character offset preservation for span computation.
- Comprehensive PEP 561 type hints (`py.typed`) with zero errors in `basedpyright` strict mode.
- Standard PEP 517/621/735 packaging via `pyproject.toml` with `hatchling` and `uv`.
- Multilingual rule sets for 22 languages: `am`, `ar`, `bg`, `da`, `de`, `el`, `en`, `es`, `fa`, `fr`, `hi`, `hy`, `it`, `ja`, `kk`, `mr`, `nl`, `pl`, `ru`, `sk`, `ur`, `zh`.
- Zero runtime dependencies.

=======
# v0.3.4
- 🐛 Fix trailing period/ellipses with spaces - #83
- 🐛 Regex escape for parenthesis - #87

# v0.3.3
- 🐛 Better handling consecutive periods and reserved special symbols - allenai/scholarphi#114
- Add CONTRIBUTING.md

# v0.3.2
- 🐛 ✅ Enforce clean=True when doc_type="pdf" - \#75

# v0.3.1
- 🚑 ✅ Handle Newline character & update tests

# v0.3.0
-   ✨ 💫  Support Multiple languages - \#2
-   🏎⚡️💯 Benchmark across Segmentation Tools, Libraries and Algorithms
-   🎨 ♻️ Update sentence char_span logic
-   ⚡️  Performance improvements - \#41
-   ♻️🐛 Refactor AbbreviationReplacer

# v0.3.0rc
-   ✨ 💫 sent `char_span` through with spaCy & regex approach - \#63
-   ♻️ Refactoring to support multiple languages
-   ✨ 💫Initial language support for - Hindi, Marathi, Chinese, Spanish
-   ✅ Updated tests - more coverage & regression tests for issues
-   👷👷🏻‍♀️ GitHub actions for CI-CD
-   💚☂️ Add code coverage - coverage.py Add Codecov
-   🐛 Fix incorrect text span & vanilla pysbd vs spacy output discrepancy - \#49, \#53, \#55 , \#59
-   🐛 Fix `NUMBERED_REFERENCE_REGEX` for zero or one time - \#58
-   🔐Fix security vulnerability bleach - \#62


# v0.2.3
-   🐛 Performance improvement in `abbreviation_replacer`- \#50

# v0.2.2
-   🐛 Fix unbalanced parenthesis - \#47

# v0.2.1
-   ✨pySBD as a spaCy component through entrypoints

# v0.2.0
-   ✨Add `char_span` parameter (optional) to get sentence & its (start, end) char offsets from original text
-   ✨pySBD as a spaCy component example
-   🐛 Fix double question mark swallow bug - \#39

# v0.1.5
-   🐛 Handle text with only punctuations - \#36
-   🐛 Handle exclamation marks at EOL- \#37

# v0.1.4
-   ✨ ✅ Handle intermittent punctuations - \#34

# v0.1.3
-   🐛 Fix `lists_item_replacer` - \#29
-   🐛 Fix & ♻️refactor `replace_multi_period_abbreviations` - \#30
-   🐛 Fix `abbreviation_replacer` - \#31
-   ✅ Add regression tests for issues

# v0.1.2
-   🐛BugFix - IndexError of `scanlists` function

# v0.1.1
-   English language support only
-   Support for oother languages - WIP

# v0.1.0
-   Initial Release
