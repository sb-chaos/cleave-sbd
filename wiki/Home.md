# cleave-sbd Wiki

Welcome to the **cleave-sbd** documentation wiki.

**cleave-sbd** is a high-performance, strictly-typed sentence boundary disambiguation (SBD) engine for Python (3.11+) with zero machine learning dependencies.

---

## Documentation Pages

- **[Common API Use Cases & Recipes](Common-Use-Cases)**: Comprehensive code recipes for sentence segmentation, exact character span extraction, unbounded streaming, noisy data cleaning, PDF repair, and multilingual usage.

---

## Quick Navigation & Resources

- **[GitHub Repository](https://github.com/sb-chaos/cleave-sbd)**: Source code, issue tracker, and CI status.
- **[PyPI Package](https://pypi.org/project/cleave-sbd/)**: Releases and downloads.
- **[Changelog](https://github.com/sb-chaos/cleave-sbd/blob/main/CHANGELOG.md)**: Release notes and version history.

---

## Key Highlights

- **Zero Heavy ML Dependencies**: Pure Python rule evaluation and pre-compiled regex automata—no PyTorch, spaCy model weights, or CUDA requirements.
- **1:1 Offset Invariance**: Length-preserving PUA sentinels ensure exact character offsets for annotation & span tracking.
- **Strict Typing**: PEP 561 compliant, verified under Basedpyright strict mode.
- **Multilingual**: Built-in support for 22 languages.
