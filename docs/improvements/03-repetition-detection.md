# Improvement 3: Repetition Detection Robustness

**Goal:** Make repetition detection robust when there are **too few** diagonal lines, **too many** noisy lines, or **conflicting** period clusters. Students implementing this improvement will add **relaxed-threshold retry**, **filtering by strength**, and **period-cluster scoring** to choose or flag ambiguous periods.

---

## 1. Concept

### Why it matters

- **Too few lines:** Strict thresholds can miss real repetitions in noisy or low-contrast SSMs. The pipeline may then fail in Stage 4 (“No repetitions found”) or produce a weak period estimate. Allowing a **one-time relaxed retry** (e.g. lower similarity threshold or shorter min length) can recover structure without changing the default behaviour.
- **Too many lines:** Very dense SSMs (e.g. static or highly repetitive) yield hundreds of short, weak diagonals. That can confuse period clustering (many small clusters) and slow down structure analysis. **Filtering** by strength (e.g. keep top percentile) or by minimum duration reduces noise.
- **Conflicting periods:** Sometimes two or more lag clusters have similar size (e.g. period P and period 2P). Picking the “largest cluster” alone may be wrong. **Scoring** each candidate period by how well it explains sub-patterns (integer divisions) and choosing the best, or **reporting ambiguity**, improves reliability.

### What to add

1. **Too few lines — relaxed retry**  
   If `find_diagonal_lines` returns fewer than a minimum (e.g. 3 or `MIN_REPETITIONS`), **once** re-run with relaxed parameters: e.g. `REPETITION_THRESHOLD - 0.1` and/or `MIN_REPETITION_DURATION * 0.5`. If the retry yields enough lines, use that result and set a flag (e.g. `repetition_relaxed_threshold_used`). If still too few, proceed with the current result and a warning.

2. **Too many lines — filtering**  
   If the number of diagonal lines exceeds a cap (e.g. 500), **filter** to the strongest or longest: sort by strength (and optionally duration), keep the top N or top percentile (e.g. 95th). Use the filtered list for Stage 4. Optionally add a warning that filtering was applied.

3. **Conflicting periods — cluster scoring**  
   In `_find_period` (or a wrapper), instead of taking only the largest cluster, **score** the top few clusters by: (a) cluster size, (b) how well the cluster’s median period explains sub-patterns (e.g. count of diagonal lines whose lag is close to an integer division of the period). Pick the period with the best score, or if two are close, set an **ambiguous_period** flag and return the primary candidate plus an alternative.

---

## 2. Potential Python libraries

| Library | Use | Documentation |
|--------|-----|----------------|
| **NumPy** | Sort lines by strength; percentile with `np.percentile`; filter by boolean mask; cluster lag times (existing logic uses sorting and tolerance). | [NumPy](https://numpy.org/doc/stable/) |
| **SciPy** | Optional: `scipy.cluster.hierarchy` or `scipy.spatial.distance` for more formal clustering of lags; not strictly required if you keep the current tolerance-based clustering. | [SciPy](https://docs.scipy.org/doc/scipy/) |

No new dependencies required; optional use of SciPy clustering for cleaner cluster scoring.

---

## 3. Flowchart of the improvement

```mermaid
flowchart TB
    subgraph Diag["find_diagonal_lines"]
        D1[ssm, times, min_length, threshold]
        D1 --> D2[Scan lags; collect line segments]
        D2 --> D3[List of diagonal_lines]
    end

    subgraph Few["Too few lines"]
        F1{len(lines) < MIN?}
        F1 -->|Yes| F2[Retry once: threshold -= 0.1 or min_length *= 0.5]
        F2 --> F3[find_diagonal_lines with relaxed params]
        F3 --> F4{len(lines) >= MIN?}
        F4 -->|Yes| F5[Use these lines; set relaxed_threshold_used]
        F4 -->|No| F6[Use original lines; add warning]
        F1 -->|No| F7[Use lines as-is]
    end

    subgraph Many["Too many lines"]
        M1{len(lines) > CAP?}
        M1 -->|Yes| M2[Sort by strength descending]
        M2 --> M3[Keep top N or top percentile]
        M3 --> M4[Filtered list to Stage 4]
        M1 -->|No| M4
    end

    subgraph Period["Period selection"]
        P1[Cluster lags by PERIOD_TOLERANCE]
        P1 --> P2[Top clusters: size and median lag]
        P2 --> P3[For each candidate period: score by sub-pattern fit]
        P3 --> P4{Two scores close?}
        P4 -->|Yes| P5[Set ambiguous_period; return best + alternative]
        P4 -->|No| P6[Return best period]
    end

    D3 --> F1
    F5 --> M1
    F6 --> M1
    F7 --> M1
    M4 --> P1
```

**Integration points:**

- **Few/many:** In `src/pipeline.py` after calling `find_diagonal_lines`: implement the “too few” retry and the “too many” filter, then pass the final list to `analyze_repetition`. Alternatively, add a wrapper function in `src/core/ssm_analysis.py` or `repetition_detection.py` that returns “filtered and possibly relaxed” lines.
- **Period scoring:** In `src/core/repetition_detection.py`, extend `_find_period` to return the top-k clusters and their medians; add a small function that scores each candidate by sub-pattern consistency (e.g. count of lines whose lag is near an integer division of the candidate). Call it from `analyze_repetition` and pass the chosen period (and optional alternative) to the rest of the structure step.

---

## 4. Implementation notes for students

- Config: `REPETITION_RELAX_THRESHOLD_DELTA`, `REPETITION_RELAX_MIN_LENGTH_FACTOR`, `MAX_DIAGONAL_LINES` (or `DIAGONAL_LINES_TOP_PERCENTILE`), and optionally `PERIOD_AMBIGUITY_SCORE_RATIO` (e.g. if second-best score is within 10% of best, set ambiguous).
- Keep the retry **one-shot** to avoid infinite relaxation. Store the parameters actually used (e.g. threshold and min_length) in the result or warnings so reports can show “relaxed threshold used”.
- For period scoring: re-use the same integer-division logic you use in `_find_sub_patterns` (period/lag ≈ integer). For each candidate period, count how many lines have lags that are “explained” by that period; use that count (or a weighted sum with cluster size) as the score.
