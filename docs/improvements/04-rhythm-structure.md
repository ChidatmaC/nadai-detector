# Improvement 4: Rhythm Structure Robustness

**Goal:** Handle cases where **no period** is found, **no or few sub-patterns** are found, and ensure results stay within **sanity bounds** (e.g. beat duration and phrase period in plausible ranges). Students implementing this improvement will add **fallback period estimation**, **explicit fallback flags**, and **sanity checks** that can trigger warnings or retries.

---

## 1. Concept

### Why it matters

- **No period:** `_find_period` can return `None` if no diagonal lines pass the strength/duration filter or if lag clustering yields no clear winner. The pipeline currently raises “Could not determine phrase period”. A **fallback** (e.g. median of all lags, or a default from config) plus a **flag** (e.g. `period_from_fallback`) lets the pipeline still produce a result while signalling lower confidence.
- **No sub-patterns:** When `_find_sub_patterns` returns an empty list, we already default to e.g. 8 beats and 4 nadai. Making this **explicit** (e.g. `structure_from_fallback`) and optionally trying an **alternative period** (e.g. second-best cluster) that yields valid integer divisions can sometimes recover a better structure.
- **Sanity bounds:** Unlikely values (e.g. beat duration 0.01 s or 30 s, phrase period 0.5 s or 5 minutes) often indicate a bug or a bad SSM. **Rejecting** or **flagging** out-of-range results and optionally **retrying** with different parameters (e.g. different period cluster) keeps output interpretable.

### What to add

1. **No period — fallback**  
   If `_find_period` returns `None`, compute a fallback: e.g. median of all lag times from diagonal lines (perhaps with a minimum count), or use a config value `DEFAULT_PHRASE_PERIOD`. Set a result flag `period_from_fallback = True` and add a warning. Continue to Stage 4 with this period.

2. **No sub-patterns — explicit flag and optional alternative period**  
   When `_find_sub_patterns` is empty, keep the current default (e.g. 8, 4.0). Set `structure_from_fallback = True` in the structure dict or result. Optionally: if we have multiple period candidates (from Improvement 3), try the **next** candidate period and re-run `_find_sub_patterns` and `_determine_structure`; if that yields sub-patterns, use that structure instead.

3. **Sanity bounds**  
   After computing `beat_duration` and `phrase_period`, check they lie in plausible ranges (e.g. beat 0.15–3 s, phrase 1–120 s). If outside: **reject** (raise) or **flag** (warning + optionally keep or replace with fallback). Optionally trigger a **retry** with the next-best period candidate if available.

---

## 2. Potential Python libraries

| Library | Use | Documentation |
|--------|-----|----------------|
| **NumPy** | Median of lags: `np.median(lag_times)`. Comparisons for bounds. | [NumPy](https://numpy.org/doc/stable/) |

No new dependencies. Logic is in `repetition_detection.py` and the pipeline.

---

## 3. Flowchart of the improvement

```mermaid
flowchart TB
    subgraph Period["Period finding"]
        P1[_find_period diagonal_lines]
        P1 --> P2{period is None?}
        P2 -->|Yes| P3[Fallback: median of all lags or DEFAULT_PHRASE_PERIOD]
        P3 --> P4[Set period_from_fallback = True]
        P4 --> P5[Continue with period]
        P2 -->|No| P5
    end

    subgraph Sub["Sub-patterns and structure"]
        S1[_find_sub_patterns lines, period]
        S1 --> S2{sub_patterns empty?}
        S2 -->|Yes| S3[Try next period candidate?]
        S3 --> S4[Re-run _find_sub_patterns with alt period]
        S4 --> S5{Has sub-patterns now?}
        S5 -->|Yes| S6[Use this structure]
        S5 -->|No| S7[Default num_beats, subdivisions; set structure_from_fallback]
        S2 -->|No| S8[_determine_structure]
        S6 --> S8
        S7 --> S8
    end

    subgraph Sanity["Sanity bounds"]
        B1[beat_duration, phrase_period]
        B1 --> B2{beat in [MIN_BEAT, MAX_BEAT]?}
        B2 -->|No| B3[Flag or reject; optional: try next period]
        B2 -->|Yes| B4{phrase in [MIN_PHRASE, MAX_PHRASE]?}
        B4 -->|No| B3
        B4 -->|Yes| B5[Accept result]
        B3 --> B6[Warning + fallback or raise]
    end

    P5 --> S1
    S8 --> B1
```

**Integration points:**

- **Fallback period:** In `analyze_repetition` in `src/core/repetition_detection.py`, when `_find_period` returns `None`, compute fallback period and set a flag; pass both into the rest of the function and include the flag in the returned dict. Pipeline can copy the flag into the final result.
- **Alternative period:** If you implement Improvement 3 (top-k period candidates), in Stage 4 try the first candidate; if sub-patterns are empty, try the next candidate before applying the default.
- **Sanity bounds:** In the pipeline, after assembling the result dict, call a helper e.g. `check_sanity_bounds(result)` that checks `beat_duration` and `phrase_period` against config constants; append to warnings or raise. Config: `BEAT_DURATION_MIN`, `BEAT_DURATION_MAX`, `PHRASE_PERIOD_MIN`, `PHRASE_PERIOD_MAX`.

---

## 4. Implementation notes for students

- Add to `config/settings.py`: `DEFAULT_PHRASE_PERIOD` (e.g. 4.0 s), `BEAT_DURATION_MIN` (0.15), `BEAT_DURATION_MAX` (3.0), `PHRASE_PERIOD_MIN` (1.0), `PHRASE_PERIOD_MAX` (120.0). Use these in repetition_detection and in the pipeline sanity check.
- Ensure the structure dict returned by `analyze_repetition` can carry `period_from_fallback` and `structure_from_fallback` so the pipeline can put them in the final result and in reports (Improvement 7).
- Sanity check: if bounds are violated, prefer **warning + keep result** first (so reports show the anomaly); add an option to **reject** (raise) for strict mode if needed.
