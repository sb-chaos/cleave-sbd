# cleave-sbd Documentation Wiki

Welcome to the **cleave-sbd** documentation and engineering wiki.

**cleave-sbd** is a high-performance, strictly-typed sentence boundary disambiguation (SBD) engine for Python (3.11+) with zero machine learning dependencies.

---

## Complete Wiki Index

1. **[Architecture & Engineering Philosophy](Architecture-and-Engineering-Philosophy)**
   The 10 core architectural invariants governing zero-dependency design, strict typing, layered decoupling, immutable modeling, and performance guarantees.

2. **[Coordinate Invariance & OffsetMap](Coordinate-Invariance-&-OffsetMap)**
   Detailed breakdown of length-preserving PUA sentinel masking and $O(\log K)$ cumulative delta tracking for exact 1:1 character span mapping back to source documents.

3. **[Common API Use Cases & Recipes](Common-Use-Cases)**
   Comprehensive code recipes for sentence segmentation, exact character span extraction, bounded memory streaming, PDF normalization, and multilingual handling.

4. **[Language Support & Heuristics](Language-Support-&-Heuristics)**
   Linguistic heuristics and edge-case handling across 22 supported languages (non-Latin punctuation, continuous scripts, legal outlines, abbreviations).

5. **[Performance & Speed Benchmarks](Performance-and-Benchmarks)**
   Comparative throughput and latency benchmarks evaluated against Stanford Stanza, spaCy, NLTK, BlingFire, Syntok, and pySBD on the Shakespeare corpus.

6. **[Contributing & Adding Languages](Contributing-&-Adding-Languages)**
   Step-by-step instructions for setting up the development environment, running automated quality gates (`validate.sh`), and adding support for new languages.

---

## Quick Navigation & Links

* **[GitHub Repository](https://github.com/sb-chaos/cleave-sbd)**: Source code, issue tracker, and CI pipelines.
* **[PyPI Package](https://pypi.org/project/cleave-sbd/)**: Official releases and installation wheels.
* **[Changelog](https://github.com/sb-chaos/cleave-sbd/blob/main/CHANGELOG.md)**: Version release notes.
