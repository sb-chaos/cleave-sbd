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

