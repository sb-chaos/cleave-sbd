# Coordinate Invariance & OffsetMap

`cleave-sbd` is engineered to maintain exact byte and character coordinate invariance between segmented sentence spans and the raw input text.

This document details the dual mechanisms that enable this:
1. **Length-Preserving PUA Sentinels** (for pure SBD in `clean=False` mode).
2. **Cumulative Delta Tracking with `OffsetMap`** (for destructive transformations in `clean=True` mode).

---

## 1. Private Use Area (PUA) Sentinel Masking

In `clean=False` mode, `cleave-sbd` modifies nothing about the source text string's length:

$$\text{len}(\text{masked\_text}) == \text{len}(\text{original\_text})$$

Periods and punctuation marks inside abbreviations, numbers, quotes, and ellipses are temporarily substituted 1:1 with single-character Unicode Private Use Area (PUA) codepoints (`\ue000`–`\ue021`):

| Punctuation Type | Character | PUA Sentinel | Codepoint |
| :--- | :---: | :---: | :---: |
| Standard Period (Abbr / Honorific) | `.` | `\ue000` | `PUA_PERIOD` |
| CJK Fullwidth Period | `。` | `\ue001` | `PUA_CJK_PERIOD` |
| Fullwidth Period | `．` | `\ue002` | `PUA_FULLWIDTH_PERIOD` |
| Exclamation Mark | `!` | `\ue004` | `PUA_EXCLAMATION` |
| Question Mark | `?` | `\ue005` | `PUA_QUESTION` |
| Ellipsis Dot | `.` | `\ue020` | `PUA_ELLIPSIS_DOT` |

Because every substitution preserves length $1:1$, slice coordinates `(start, end)` extracted from `masked_text` map directly to `original_text[start:end]`. Once boundaries are identified, `unmask_all()` restores sentinels in a single C-level `.translate()` pass.

---

## 2. Cumulative Delta Tracking (`OffsetMap`)

When `clean=True` is requested, the text undergoes destructive normalization (HTML stripping, quote fixes, hyphenated line-break repair, and whitespace normalization). These changes alter the length of the string buffer.

To maintain exact coordinate linkage back to the raw source document, `cleave-sbd` tracks every length modification inside an immutable **`OffsetMap`**.

### How the Coordinate Projection Works

```
Raw Source Text (Length = 39):
[0]                                                    [38]
 v                                                      v
"<p>Hello world! This is a test sentence.</p>"

Transformations Applied:
 1. Strip '<p>'  at raw [0:3]   -> Net shift: +3 chars deleted
 2. Strip '</p>' at raw [35:39] -> Net shift: +4 chars deleted (Total cumulative delta: +7)

Cleaned Text Buffer (Length = 32):
[0]                                  [31]
 v                                    v
"Hello world! This is a test sentence."

OffsetMap Internal Arrays:
  clean_keys:  ( 0,  32 )
  cum_deltas:  ( 3,   7 )
```

### Projection via `bisect_right` ($O(\log K)$)

When sentence boundaries are found in the cleaned buffer (e.g. `Sentence 1: [0:12]`, `Sentence 2: [13:32]`), `OffsetMap.clean_span_to_raw_span()` projects them back to raw coordinates in $O(\log K)$ time:

```python
# Project Clean Span [0:12] ("Hello world!")
raw_start = offset_map.clean_to_raw(0)  # 0  + 3 = 3  (points to 'H' in raw)
raw_end = offset_map.clean_to_raw(12)  # 12 + 3 = 15 (points to '!' in raw)
# -> Raw Span: [3:15] matches raw text: "<p>[Hello world!] This is..."

# Project Clean Span [13:32] ("This is a test sentence.")
raw_start = offset_map.clean_to_raw(13)  # 13 + 3 = 16 (points to 'T' in raw)
raw_end = offset_map.clean_to_raw(32)  # 32 + 7 = 39 (points to end in raw)
# -> Raw Span: [16:39] matches raw text: "...[This is a test sentence.]</p>"
```

---

## 3. The `TextSpan` Structure

When `char_span=True` is enabled, sentences are returned as immutable, slotted [`TextSpan`](models.py) objects carrying dual coordinates:

```python
@dataclass(slots=True, frozen=True)
class TextSpan:
    sent: str  # Normalized sentence string (for LLMs / NLP models)
    start: int  # Raw original document start index (for UI highlights)
    end: int  # Raw original document end index (for UI highlights)
    clean_start: int | None  # Cleaned buffer start index (optional)
    clean_end: int | None  # Cleaned buffer end index (optional)
    raw_slice: str | None  # Raw uncleaned slice text[start:end] (optional)
```

This guarantees:
1. **Downstream NLP models & LLMs** receive clean, tag-free sentence text via `span.sent`.
2. **Frontend UI renderers & PDF viewers** receive exact source coordinates (`span.start`, `span.end`) to paint highlights onto the original document without offset drift.
