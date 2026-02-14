# Improvement 5: Nadai Classification Robustness

**Goal:** When the classifier returns **“unknown”** nadai or when the subdivision count is ambiguous, provide a **fallback** (e.g. nearest known nadai) and a **confidence score** so callers and reports can show reliability. Students implementing this improvement will add **unknown-nadai handling** and a **nadai confidence** based on distance to known definitions.

---

## 1. Concept

### Why it matters

- **Unknown nadai:** The current classifier maps a rounded integer `n` to a nadai name using `NADAI_DEFINITIONS` and divisibility rules. If no rule matches (e.g. n=11), it returns `('unknown', n)`. For downstream use (reports, UI), it is helpful to either (a) **map to the nearest known** nadai (e.g. 11 → caturasra 12 with a note), or (b) **keep unknown** but attach a **confidence** so the user knows the result is uncertain.
- **Confidence:** Even when we return a known nadai, the **subdivisions_per_beat** from the structure step is a float; we round to an integer. How close that float is to the integer (and to the nearest definition) is a proxy for confidence. Exposing a **nadai_confidence** (e.g. 0–1) helps filter or flag low-confidence results.

### What to add

1. **Unknown nadai — nearest known**  
   When the classifier would return `unknown`, compute the **closest** known nadai value (from all multiples in `NADAI_DEFINITIONS`) by minimum absolute difference. Return that nadai name and value, plus a flag e.g. `nadai_nearest_fallback = True` and optionally the original `n`. Alternatively, keep `unknown` but add a suggested “nearest” in the result for display.

2. **Confidence score**  
   Define **nadai_confidence** as a function of: (a) how close `subdivisions_per_beat` is to an integer, and (b) how close that integer is to a known nadai multiple (e.g. distance in “multiples” or normalised). For example: if we have an exact match, confidence 1.0; if we used nearest fallback, cap at 0.7; if the float is far from an integer, reduce further. Add `nadai_confidence` to the result dict and optionally to the report.

---

## 2. Potential Python libraries

| Library | Use | Documentation |
|--------|-----|----------------|
| **NumPy** | `np.abs`, `np.argmin` to find nearest value in a list of known multiples; no new dependency. | [NumPy](https://numpy.org/doc/stable/) |

No new dependencies. All logic in `src/core/nadai_classifier.py` and the pipeline.

---

## 3. Flowchart of the improvement

```mermaid
flowchart TB
    subgraph Classify["classify_nadai"]
        C1[subdivisions_per_beat float]
        C1 --> C2[n = round float]
        C2 --> C3[Match in NADAI_DEFINITIONS?]
        C3 -->|Yes| C4[Return nadai_name, n]
        C3 -->|No| C5[Divisibility rules]
        C5 --> C6{Matched?}
        C6 -->|Yes| C4
        C6 -->|No| C7[unknown, n]
    end

    subgraph New["New: unknown and confidence"]
        N1[If unknown: collect all multiples from NADAI_DEFINITIONS]
        N1 --> N2[Find value with min |n - mult|]
        N2 --> N3[Return that nadai + nadai_nearest_fallback=True]
        N3 --> N4[Compute confidence]
        N4 --> N5[Distance to integer: 1 - |float - round(float)|]
        N5 --> N6[Distance to known: 0 if exact else 1 - normalised_dist]
        N6 --> N7[Combine: e.g. min or product]
        N7 --> N8[If fallback used: cap confidence]
        N8 --> N9[Add nadai_confidence to result]
    end

    C7 --> N1
    C4 --> N4
    N3 --> N4
```

**Integration points:**

- **Nearest known:** In `classify_nadai`, when you would return `('unknown', n)`, instead (or in addition) compute the nearest multiple across all definitions; return e.g. `(nadai_name, nearest_value, nadai_nearest_fallback=True)`. The pipeline then stores both the primary classification and the flag.
- **Confidence:** Add a helper e.g. `compute_nadai_confidence(subdivisions_per_beat, nadai_name, nadai_value, used_fallback)` that returns a float in [0, 1]. Call it in the pipeline after `classify_nadai` and add `nadai_confidence` to the result dict. Optionally reduce confidence when `structure_from_fallback` is True (from Improvement 4).

---

## 4. Implementation notes for students

- **Signature change:** You can keep `classify_nadai` returning `(name, value)` and add an optional third element or a separate function `classify_nadai_with_confidence` that returns `(name, value, confidence, flags)`. Or keep the same return and compute confidence in the pipeline from the inputs and return value.
- **Config:** Optionally add `NADAI_CONFIDENCE_FALLBACK_CAP` (e.g. 0.7) when nearest fallback was used.
- **Report:** In `generate_report` (or in the template), add a line for `nadai_confidence` and a note when `nadai_nearest_fallback` is True so users see that the result was inferred.
