# cleave-sbd Documentation Wiki

Welcome to the **cleave-sbd** documentation and engineering wiki.

**cleave-sbd** is a high-performance, strictly-typed sentence boundary disambiguation (SBD) engine for Python (3.11+) with zero machine learning dependencies.

---

## Complete Wiki Index

1. **[Design Philosophy](Design-Philosophy)**
   The 10 design rules behind our zero-dependency build, strict typing, and memory model.

2. **[Span Tracking](Span-Tracking)**
   The mechanics behind our PUA masks and $O(\log K)$ delta tracking for exact character offsets.

3. **[Use Cases](Use-Cases)**
   Code recipes for sentence segmentation, span extraction, bounded streaming, and data cleaning.

4. **[Languages](Languages)**
   How we handle abbreviations, legal numbering, non-Latin scripts, and unspaced text across 22 languages.

5. **[Benchmarks](Benchmarks)**
   Benchmark comparisons, latency tables, and failure analysis against Stanza, spaCy, NLTK, BlingFire, Syntok, and pySBD.

6. **[Contributing](Contributing)**
   Developer guide for running automated quality gates (`validate.sh`) and adding language configurations.

---

## Quick Navigation & Links

* **[GitHub Repository](https://github.com/sb-chaos/cleave-sbd)**: Source code, issue tracker, and CI pipelines.
* **[PyPI Package](https://pypi.org/project/cleave-sbd/)**: Official releases and installation wheels.
* **[Changelog](https://github.com/sb-chaos/cleave-sbd/blob/main/CHANGELOG.md)**: Version release notes.
