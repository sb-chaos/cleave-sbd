# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.2.0-beta.1] - 2026-08-24

### Added
- **Memory-Bounded Sentence Streaming API**: Introduced `Segmenter.stream(text, chunk_paragraphs=1000)` lazy generator for constant-memory corpus processing with exact global character offset tracking (`TextSpan`).
- **Modular Processor Architecture**: Decomposed monolithic disambiguator into specialized single-responsibility modules:
  - `csbd.processors.lists`: AST-based sequential validation for numbered, alphabetical, and Roman numeral lists.
  - `csbd.processors.abbreviation`: LRU-cached category compilation, prepositive matching, and linguistic abbreviation masking.
  - `csbd.disambiguator`: Lean, functional pipeline orchestrator.
- **Rules Package Separation**: Extracted all pre-compiled regex tables, PUA sentinels, and replacement definitions into `csbd.rules`.
- **ReDoS Hardening & Catastrophic Backtracking Defenses**: Audited and hardened nested lookahead/group expressions with non-backtracking atomic lookaheads, backed by `tests/test_backtracking.py`.
- **Benchmarking & Profiling Suite**: Added `profiling/profile_benchmarks.py` for automated profiling and throughput benchmarking.

### Changed
- **Package Layout & Rebranding**: Migrated from `pragmatic_sbd` to `cleave-sbd` under standard `src/` directory layout.
- **$O(1)$ Hash Set Scanner Optimization**: Replaced massive 100+ branch regex alternations with single-pass word boundary scanners (`STANDARD_ABBR_SCAN_REGEX`) and compiled C-level `frozenset` lookups.
- **Fast-Path Character Short-Circuiting**: Added SIMD `str.__contains__` (`memchr`) short-circuiting to skip unused paired delimiter and punctuation regex passes.
- **Zero-Allocation Span Tracking**: Replaced heap-allocated `.strip()` / `.lstrip()` operations in `trim_span` with pointer index scanning, eliminating over 700,000 intermediate string allocations.
- **Single-Pass Acronym Matching**: Optimized uppercase initial parsing to match arbitrary consecutive initials in a single pass (`(?:[A-ZА-ЯЁ]\.)+`).
- **Documentation & Typing**: Added full Google-style docstrings and normalized all variables across the codebase, maintaining zero errors in `basedpyright` strict mode.
- **Externalized Test Suite**: Converted test fixtures to structured `.toml` datasets with strongly typed `NamedTuple` boundaries.

### Performance
- Single-threaded throughput increased to **>1.3 MB/s** (~3.45s unprofiled execution on 5.13 MB / 176,000 sentences).

---

## [0.1.0] - 2026-08-18

### Added
- Complete modern rewrite and architecture of the sentence boundary disambiguation engine.
- Declarative, pre-compiled regular expression pipeline replacing procedural loops.
- Pure functional, length-preserving Private Use Area (PUA) sentinel substitutions (`\ue000`–`\ue009`) guaranteeing $1:1$ character offset preservation for span computation.
- Comprehensive PEP 561 type hints (`py.typed`) with zero errors in `basedpyright` strict mode.
- Standard PEP 517/621/735 packaging via `pyproject.toml` with `hatchling` and `uv`.
- Multilingual rule sets for 22 languages: `am`, `ar`, `bg`, `da`, `de`, `el`, `en`, `es`, `fa`, `fr`, `hi`, `hy`, `it`, `ja`, `kk`, `mr`, `nl`, `pl`, `ru`, `sk`, `ur`, `zh`.
- Zero runtime dependencies.

