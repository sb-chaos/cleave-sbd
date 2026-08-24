# Common API Use Cases & Recipes

This guide covers common patterns and recipes for using `cleave-sbd` across various real-world scenarios.

---

## 1. Basic Sentence Segmentation

For standard text processing pipelines where you need pure sentence strings with abbreviations, numbers, and quotations handled accurately.

```python
import csbd

text = (
    "Dr. Watson arrived at 221B Baker St. at 5:30 p.m. "
    "He asked, 'Is Mr. Holmes available?' The maid said yes."
)

segmenter = csbd.Segmenter(language="en", clean=False)
sentences = segmenter.segment(text)

for i, sent in enumerate(sentences, 1):
    print(f"{i}: {sent}")
```

**Output:**
```text
1: Dr. Watson arrived at 221B Baker St. at 5:30 p.m.
2: He asked, 'Is Mr. Holmes available?' The maid said yes.
```

---

## 2. Character Span Extraction (Exact Source Offsets)

Use `char_span=True` when building annotation tools, highlighting interfaces, or entity extractors where you must map each sentence back to exact `[start:end]` character slices in the raw document without altering source text.

```python
import csbd

text = "Visit U.S.A. today! See item no. 4 on p. 12."
segmenter = csbd.Segmenter(language="en", char_span=True)

spans = segmenter.segment(text)
for span in spans:
    print(f"Span [{span.start}:{span.end}]: {span.sent}")
    # Verify exact slice match:
    assert text[span.start : span.end] == span.sent
```

**Output:**
```text
Span [0:19]: Visit U.S.A. today!
Span [20:45]: See item no. 4 on p. 12.
```

---

## 3. Streaming Large Corpora (Bounded Memory)

For multi-megabyte corpora, books, or database dumps, use `.stream()` to yield sentences lazily per paragraph chunk instead of loading all segmented tuples into memory at once.

```python
import csbd

segmenter = csbd.Segmenter(language="en")

with open("large_corpus.txt", "r", encoding="utf-8") as f:
    text = f.read()

# Yields sentences incrementally per 500 paragraphs
for sent in segmenter.stream(text, chunk_paragraphs=500):
    process_sentence(sent)
```

You can also combine streaming with character offsets:

```python
segmenter = csbd.Segmenter(language="en", char_span=True)
for span in segmenter.stream(text, chunk_paragraphs=500):
    print(f"[{span.start}:{span.end}] {span.sent}")
```

---

## 4. Cleaning Noisy Text & Normalization

When dealing with uncleaned raw data containing stray HTML tags, broken quote characters, or consecutive leader dots (e.g. table-of-contents), enable `clean=True`.

```python
import csbd

noisy_text = "<p>First sentence.... Chapter 1...... p. 55</p>Second sentence."
segmenter = csbd.Segmenter(language="en", clean=True)

sentences = segmenter.segment(noisy_text)
print(sentences)
# ('First sentence.', 'Chapter 1.', 'p. 55', 'Second sentence.')
```

---

## 5. Handling PDF / OCR Extracted Text

OCR and PDF extractions frequently contain unnatural hard line breaks in the middle of sentences. Set `doc_type="pdf"` (with `clean=True`) to automatically repair wrapped lines and bullet formats.

```python
import csbd

pdf_text = "This is a sentence that was bro-\nken by a column wrap.\nAnother sentence."
segmenter = csbd.Segmenter(language="en", clean=True, doc_type="pdf")

sentences = segmenter.segment(pdf_text)
print(sentences)
# ('This is a sentence that was broken by a column wrap.', 'Another sentence.')
```

---

## 6. Multilingual Disambiguation

`cleave-sbd` supports 22 languages with language-specific rules, honorifics, abbreviations, and punctuation sets.

```python
import csbd

# German (handles German honorifics like 'Hr.', 'Fr.', 'z.B.')
de_seg = csbd.Segmenter(language="de")
print(de_seg.segment("Hr. Schmidt geht nach Hause. Es ist 18 Uhr."))
# ('Hr. Schmidt geht nach Hause.', 'Es ist 18 Uhr.')

# Japanese (handles full-width punctuation '。', '！', '？')
ja_seg = csbd.Segmenter(language="ja")
print(ja_seg.segment("今日はいい天気ですね。散歩に行きましょう！楽しかったです。"))
# ('今日はいい天気ですね。', '散歩に行きましょう！', '楽しかったです。')

# Spanish (handles inverted question/exclamation marks '¿', '¡')
es_seg = csbd.Segmenter(language="es")
print(es_seg.segment("¡Hola! ¿Cómo estás? Estoy bien."))
# ('¡Hola!', '¿Cómo estás?', 'Estoy bien.')
```

---

## 7. Direct Lower-Level Functional API

For maximum control, you can import and call `disambiguate` or `normalize` directly without instantiating the `Segmenter` class.

```python
from csbd import disambiguate, normalize
from csbd.language import get_language_module

config = get_language_module("en")

# 1. Custom normalization stage
cleaned = normalize("<p>Some text.</p>", config=config)

# 2. Direct offset tuple extraction: returns ((start, end), ...)
raw_offsets = disambiguate(
    "Hello world! Here is Dr. Watson.", config=config, char_span=True
)
print(raw_offsets)
# ((0, 12), (13, 32))
```

---

## Summary of Constraints & Invariants

| Configuration | Allowed? | Rationale / Behavior |
| --- | :---: | --- |
| `Segmenter(clean=False, char_span=True)` | ✅ | Retains $1:1$ character indexing with original source text. |
| `Segmenter(clean=True, char_span=True)` | ❌ | Raises `ValueError` — cleaning mutates the string, invalidating offsets. |
| `Segmenter(clean=True, doc_type="pdf")` | ✅ | Reconnects broken PDF line wraps and removes mid-word hyphens. |
| `Segmenter(clean=False, doc_type="pdf")` | ❌ | Raises `ValueError` — PDF repair requires active cleaning. |
