# cleave-sbd: Sentence Boundary Disambiguation

[![python-package](https://github.com/sb-chaos/cleave-sbd/actions/workflows/python-package.yml/badge.svg)](https://github.com/sb-chaos/cleave-sbd/actions/workflows/python-package.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python: 3.11+](https://img.shields.io/badge/python-3.11%2B-blue.svg)](https://www.python.org/downloads/)
[![Dependencies: None](https://img.shields.io/badge/dependencies-0%20(stdlib)-brightgreen.svg)](#features)
[![Typing: Strict](https://img.shields.io/badge/typing-strict-green.svg)](https://peps.python.org/pep-0561/)
[![Code Style: Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)

**cleave-sbd** is a high-performance, strictly-typed sentence boundary disambiguation (SBD) engine. It isolates sentence boundaries across abbreviations, honorifics, numbers, lists, ellipses, and quotations without machine learning dependencies.

---

## Features

* **Zero Heavy Dependencies:** Pure Python logic without neural models, PyTorch, or GPU requirements.
* **Length-Preserving Coordinate Mapping:** PUA sentinel substitutions and offset delta tracking ensure 1:1 character offset invariance for precise span extraction.
* **Strict Typing:** Fully typed and verified in strict mode with Basedpyright/Pyright (PEP 561 compliant with `py.typed`).
* **Multilingual Support:** Out-of-the-box rule sets for 22 languages.
* **High Performance:** Pre-compiled regular expressions and immutable lookup tables.

---

## Installation

```bash
pip install cleave-sbd
```

Or with `uv`:

```bash
uv add cleave-sbd
```

---

## Quickstart

```python
import csbd

text = "My name is Jonas E. Smith. Please turn to p. 55."
seg = csbd.Segmenter(language="en", clean=False)

sentences = seg.segment(text)
print(sentences)
# Output:
# ('My name is Jonas E. Smith.', 'Please turn to p. 55.')
```

### Character Span Mode

Extract start and end character offsets alongside segmented sentences:

```python
import csbd

text = "Hello world! This is a test."
seg = csbd.Segmenter(language="en", char_span=True)

spans = seg.segment(text)
for span in spans:
    print(f"{span.sent!r} -> [{span.start}:{span.end}]")
# Output:
# 'Hello world!' -> [0:12]
# 'This is a test.' -> [13:28]
```

### Streaming Mode

Lazily process large texts or documents paragraph-by-paragraph with bounded memory:

```python
import csbd

seg = csbd.Segmenter(language="en")
for sentence in seg.stream(large_text, chunk_paragraphs=1000):
    print(sentence)
```

### Parallel Processing (Multi-Worker Safe) *(Coming Soon)*

Native multi-core batch processing leveraging pure immutable state machines across worker processes.

---

## Parameters

| Parameter | Type | Default | Description |
| --- | --- | --- | --- |
| `language` | `str` | `"en"` | Two-letter ISO 639-1 language code (e.g., `"en"`, `"de"`, `"fr"`, `"es"`, `"ja"`). |
| `clean` | `bool` | `False` | When `True`, normalizes noisy formatting (e.g., consecutive whitespace, unusual line breaks) before splitting. |
| `doc_type` | `str` | `""` | Set to `"pdf"` for OCR/PDF extracted line break handling (requires `clean=True`). |
| `char_span` | `bool` | `False` | When `True`, returns character offset spans (`TextSpan`) with exact coordinates projected back to the raw source document. |

---

## Supported Languages

| Code | Language | Code | Language | Code | Language |
| --- | --- | --- | --- | --- | --- |
| `am` | Amharic | `el` | Greek | `mr` | Marathi |
| `ar` | Arabic | `en` | English | `nl` | Dutch |
| `bg` | Bulgarian | `es` | Spanish | `pl` | Polish |
| `da` | Danish | `fa` | Persian | `ru` | Russian |
| `de` | German | `fr` | French | `sk` | Slovak |
| `hy` | Armenian | `hi` | Hindi | `ur` | Urdu |
| `it` | Italian | `ja` | Japanese | `zh` | Chinese |
| `kk` | Kazakh |  |  |  |  |

## Why cleave-sbd?

| Feature | `cleave-sbd` | `pySBD` | `spaCy` (sm) | `NLTK` (Punkt) |
| :--- | :---: | :---: | :---: | :---: |
| **Dependencies** | **0 (Stdlib)** | 0 | Heavy (ML/C) | 1+ (Data downloads) |
| **Typing** | **Strict (PEP 561)** | Partial | Strict | Loose / Dynamic |
| **Memory Footprint** | **Constant $O(\text{chunk})$** | Variable | Large (~50MB+) | Medium |
| **1:1 Span Projection** | **Yes (`OffsetMap`)** | Basic | Token-based | Manual slice |
| **Python Target** | **3.11+ Native** | Legacy 3.x | 3.9+ | Legacy 3.x |

---

## Documentation & Deep Dives

For complete documentation, architectural specifications, and recipes, see the **[cleave-sbd Wiki](https://github.com/sb-chaos/cleave-sbd/wiki)**:

* **[1. Architecture & Engineering Philosophy](https://github.com/sb-chaos/cleave-sbd/wiki/Architecture-and-Engineering-Philosophy)**: The 10 core architectural invariants governing zero-dependency design, strict typing, layered decoupling, and immutable modeling.
* **[2. Coordinate Invariance & OffsetMap](https://github.com/sb-chaos/cleave-sbd/wiki/Coordinate-Invariance-&-OffsetMap)**: Mechanism of length-preserving PUA sentinels and $O(\log K)$ cumulative delta tracking for exact span projection.
* **[3. Common API Use Cases & Recipes](https://github.com/sb-chaos/cleave-sbd/wiki/Common-Use-Cases)**: Code recipes for sentence segmentation, exact character span extraction, bounded streaming, and PDF repair.
* **[4. Language Support & Heuristics](https://github.com/sb-chaos/cleave-sbd/wiki/Language-Support-&-Heuristics)**: Linguistic heuristics across 22 supported languages (non-Latin scripts, legal outlines, continuous text, abbreviations).
* **[5. Performance & Speed Benchmarks](https://github.com/sb-chaos/cleave-sbd/wiki/Performance-and-Benchmarks)**: Benchmark comparisons, latency tables, and failure analysis against Stanford Stanza, spaCy, NLTK, BlingFire, Syntok, and pySBD.
* **[6. Contributing & Adding Languages](https://github.com/sb-chaos/cleave-sbd/wiki/Contributing-&-Adding-Languages)**: Developer guide for running automated quality gates (`validate.sh`) and adding language configurations.

---

## Acknowledgments & Attribution

`cleave-sbd` is an independent, complete rewrite designed from the ground up as a modern, declarative, strictly-typed sentence boundary disambiguation engine.

Sincere attribution and gratitude are given to the projects whose compiled linguistic heuristics and rule sets inspired this library:

* **[Pragmatic Segmenter](https://github.com/diasks2/pragmatic_segmenter)** by Kevin S. Dias (Ruby)
* **[pySBD](https://github.com/nipunsadvilkar/pySBD)** by Nipun Sadvilkar (Python)

---

## License

MIT License. See [LICENSE](LICENSE) for details.
