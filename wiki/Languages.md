# Languages & Rule Heuristics

`cleave-sbd` supports 22 languages out of the box with zero external models, neural tokenizers, or data downloads. Here is how we handle punctuation marks, abbreviations, and typography across scripts.

---

## 1. Supported Languages Matrix

| Code | Language | Script | Sentence Delimiters | Special Handling |
| :--- | :--- | :--- | :--- | :--- |
| `am` | Amharic | Ge'ez | `።`, `፧`, `፨` | Word space delimiter `፡`, Ge'ez numerics |
| `ar` | Arabic | Arabic | `؟`, `!`, `.` | Right-to-left layout, Arabic comma `،` protection |
| `bg` | Bulgarian | Cyrillic | `.`, `!`, `?` | Cyrillic abbreviations, initials, title honorifics |
| `da` | Danish | Latin | `.`, `!`, `?` | Danish abbreviations (`f.eks.`, `bl.a.`, `d.s.`) |
| `de` | German | Latin | `.`, `!`, `?` | German honorifics (`Hr.`, `Fr.`), ordinal numbers (`1.`, `2.`), Kommanditgesellschaft |
| `el` | Greek | Greek | `.`, `!`, `;` | Greek question mark `;`, Greek title abbreviations |
| `en` | English | Latin | `.`, `!`, `?` | Honorifics, acronyms, numbered lists, dialogue quotes, footnote citations |
| `es` | Spanish | Latin | `.`, `!`, `?` | Inverted punctuation (`¡...!` and `¿...?`), Spanish honorifics (`Sr.`, `Dña.`) |
| `fa` | Persian | Arabic-Persian | `؟`, `!`, `.` | Persian full stop and question markers |
| `fr` | French | Latin | `.`, `!`, `?` | French guillemets (`«...»`), titles (`Mme`, `Mlle`), spaced punctuation |
| `hi` | Hindi | Devanagari | `।`, `॥`, `?`, `!` | Devanagari Danda `।` and Double Danda `॥` |
| `hy` | Armenian | Armenian | `։`, `!`, `?` | Armenian full stop Verjaket `։` |
| `it` | Italian | Latin | `.`, `!`, `?` | Italian abbreviations (`Dott.`, `Prof.`, `Ing.`) |
| `ja` | Japanese | CJK | `。`, `！`, `？` | Fullwidth CJK periods `。`, Japanese brackets `「...」`, unspaced boundary splitting |
| `kk` | Kazakh | Cyrillic | `.`, `!`, `?` | Kazakh Cyrillic abbreviations |
| `mr` | Marathi | Devanagari | `।`, `?`, `!` | Devanagari Danda `।` and Marathi abbreviations |
| `my` | Burmese | Myanmar | `။`, `၊` | Myanmar Section `။` and Little Section `၊` |
| `nl` | Dutch | Latin | `.`, `!`, `?` | Dutch abbreviations (`bijv.`, `t.a.v.`, `blz.`) |
| `pl` | Polish | Latin | `.`, `!`, `?` | Polish honorifics (`np.`, `itd.`, `prof.`) |
| `ru` | Russian | Cyrillic | `.`, `!`, `?` | Russian initials (`А.С. Пушкин`), Cyrillic acronyms |
| `sk` | Slovak | Latin | `.`, `!`, `?` | Slovak abbreviations and ordinal forms |
| `ur` | Urdu | Arabic-Urdu | `۔`, `؟`, `!` | Urdu full stop `۔` and Arabic question mark `؟` |
| `zh` | Chinese | CJK | `。`, `！`, `？` | Fullwidth CJK punctuation, Chinese dialogue quotes `“...”` |

---

## 2. Common Edge-Case Heuristics

### A. Unspaced & CJK Text (Japanese, Chinese)
Japanese (`。`) and Chinese (`。`) do not require whitespace between sentences. The engine splits on fullwidth punctuation boundaries directly in the character stream without losing punctuation.

### B. Non-Latin Delimiters (Hindi, Armenian, Arabic, Urdu)
Hindi Danda (`।`), Double Danda (`॥`), and Armenian Verjaket (`։`) are treated as primary sentence boundaries while protecting nested quotes and abbreviations.

### C. Numbered Lists & Legal Outlines
The engine separates list enumerations (`1. First item`, `a. Sub-item`, `(iv) Clause`) from real sentence boundaries. Numeric decimals (`3.14159`), software versions (`v0.2.0`), currency (`$5.99`), and timestamps (`10:30 a.m.`) are protected from false splits.

### D. Abbreviations, Initials, & Honorifics
Multi-period acronyms (`U.S.A.`, `e.g.`, `Ph.D.`) are disambiguated using pre-compiled regex tables. Names with single-letter initials (e.g. `J. K. Rowling`, `George W. Bush`) are identified via prepositive heuristics so names are never broken apart.

### E. Quotations & Dialogue Spans
Punctuation enclosed within single quotes, double quotes, arrow guillemets (`«...»`), and slanted quotes (`“...”`) is masked. Trailing quotation marks after terminating punctuation (e.g. `"Hello!" said Holmes.`) are split correctly without stranding orphaned quotes.
