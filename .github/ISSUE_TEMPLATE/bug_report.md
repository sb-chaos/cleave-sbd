---
name: Bug Report
about: Report a bug or incorrect sentence boundary segmentation
title: "[BUG]: "
labels: ["bug"]
assignees: ""
---

### Problem Description
<!-- Brief description of the issue or unexpected behavior -->

### Minimal Reproducible Example
```python
import csbd

seg = csbd.Segmenter(language="en", clean=False, char_span=False)
text = "..."

print(seg.segment(text))
```

### Output Comparison

**Expected output:**
```python
["Expected sentence 1.", "Expected sentence 2."]
```

**Actual output:**
```python
["Actual output produced."]
```

### Environment
- **OS:** <!-- e.g., Ubuntu 22.04, macOS Sonoma, Windows 11 -->
- **Python version:** <!-- e.g., 3.12.2 -->
- **`cleave-sbd` version:** <!-- e.g., 0.2.0b1 -->

### Traceback / Logs (optional)
<details>
<summary>Click to view traceback</summary>

```text
<!-- Paste traceback here if applicable -->
```
</details>
