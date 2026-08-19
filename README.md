# pragmatic-sbd: Pragmatic Sentence Boundary Disambiguation

[![CI](https://github.com/sblasing/pragmatic-sbd/actions/workflows/python-package.yml/badge.svg)](https://github.com/sblasing/pragmatic-sbd/actions/workflows/python-package.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python: 3.11+](https://img.shields.io/badge/python-3.11%2B-blue.svg)](https://www.python.org/downloads/)
[![Typing: Strict](https://img.shields.io/badge/typing-strict-green.svg)](https://peps.python.org/pep-0561/)
[![Code Style: Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)

**pragmatic-sbd** is a high-performance, strictly-typed sentence boundary disambiguation (SBD) engine. It isolates sentence boundaries across complex edge cases—including abbreviations, honorifics, numbers, lists, ellipses, and quotations—with zero machine learning dependencies.

---

## Features

* **Zero Heavy Dependencies:** Pure Python logic without bloated neural models, PyTorch, or GPU requirements.
* **Declarative & Length-Preserving:** Length-preserving PUA sentinel substitutions ensure $1:1$ character offset invariance for precise span extraction.
* **Strictly Typed:** Fully typed and verified in strict mode with Basedpyright/Pyright (PEP 561 compliant with `py.typed`).
* **Multilingual Support:** Out-of-the-box rule sets for 22 languages.
* **High Performance:** Pre-compiled regular expressions and immutable lookup tables.

---

## Installation

```bash
pip install pragmatic-sbd
```

Or with `uv`:

```bash
uv add pragmatic-sbd
```

---

## Quickstart

```python
import pragmatic_sbd

text = "My name is Jonas E. Smith. Please turn to p. 55."
seg = pragmatic_sbd.Segmenter(language="en", clean=False)

sentences = seg.segment(text)
print(sentences)
# Output:
# ['My name is Jonas E. Smith.', 'Please turn to p. 55.']
```

### Character Span Mode

Extract start and end character offsets alongside segmented sentences:

```python
import pragmatic_sbd

text = "Hello world! This is a test."
seg = pragmatic_sbd.Segmenter(language="en", char_span=True)

spans = seg.segment(text)
for span in spans:
    print(f"{span.sent!r} -> [{span.start}:{span.end}]")
# Output:
# 'Hello world!' -> [0:12]
# 'This is a test.' -> [13:28]
```

---

## Parameters

| Parameter | Type | Default | Description |
| --- | --- | --- | --- |
| `language` | `str` | `"en"` | Two-letter ISO 639-1 language code (e.g., `"en"`, `"de"`, `"fr"`, `"es"`, `"ja"`). |
| `clean` | `bool` | `False` | When `True`, normalizes noisy formatting (e.g., consecutive whitespace, unusual line breaks) before splitting. |
| `doc_type` | `str` | `""` | Set to `"pdf"` for OCR/PDF extracted line break handling. Requires `clean=True`. |
| `char_span` | `bool` | `False` | When `True`, returns character offset spans (`TextSpan`) instead of plain strings. |

---

## Supported Languages

| Code | Language | Code | Language | Code | Language |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `am` | Amharic | `el` | Greek | `mr` | Marathi |
| `ar` | Arabic | `en` | English | `nl` | Dutch |
| `bg` | Bulgarian | `es` | Spanish | `pl` | Polish |
| `da` | Danish | `fa` | Persian | `ru` | Russian |
| `de` | German | `fr` | French | `sk` | Slovak |
| `hy` | Armenian | `hi` | Hindi | `ur` | Urdu |
| `it` | Italian | `ja` | Japanese | `zh` | Chinese |
| `kk` | Kazakh | | | | |

## Acknowledgments & Attribution

`pragmatic-sbd` is an independent, complete rewrite designed from the ground up as a modern, declarative, strictly-typed sentence boundary disambiguation engine.

Sincere attribution and gratitude are given to the projects whose compiled linguistic heuristics and rule sets inspired this library:
* **[Pragmatic Segmenter](https://github.com/diasks2/pragmatic_segmenter)** by Kevin S. Dias (Ruby)
* **[pySBD](https://github.com/nipunsadvilkar/pySBD)** by Nipun Sadvilkar (Python)

---

## License

MIT License. See [LICENSE](LICENSE) for details.
