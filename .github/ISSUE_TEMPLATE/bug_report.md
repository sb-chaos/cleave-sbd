---
name: Bug Report
about: Create a report and test case to help us improve pragmatic-sbd
title: "[BUG] "
labels: ["bug"]
assignees: ""

---

### Description
A clear and concise description of what the bug is.

### Reproduction Code

```python
import pragmatic_sbd

seg = pragmatic_sbd.Segmenter(language="en", clean=False, char_span=False)
text = "Your sample text here."
sentences = seg.segment(text)
print(sentences)
```

### Expected Behavior
A clear and concise description of what sentences should have been segmented.

```python
["Expected sentence 1.", "Expected sentence 2."]
```

### Actual Behavior
The actual output returned by `pragmatic-sbd`.

```python
["Actual sentence 1."]
```

### Environment Information
- Python version (e.g., `3.11.8`, `3.12.2`):
- `pragmatic-sbd` version (e.g., `0.1.0`):
- Operating System (e.g., Linux, macOS, Windows):

### Additional Context
Add any other context, stack traces, or screenshots here.

<details>
<summary>Traceback (if applicable)</summary>

```
Paste traceback here
```

</details>

