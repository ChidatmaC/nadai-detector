# Improvement 2: Feature and SSM Quality

**Goal:** Detect when features or the self-similarity matrix are degenerate (e.g. flat, no structure) and either **warn**, **skip**, or **automatically retry** with a different feature type so the pipeline does not produce meaningless nadai results. Students implementing this improvement will add **flat-feature checks**, **SSM “no structure” detection**, and **automatic feature-type fallback**.

---

## 1. Concept

### Why it matters

- **Features:** If the audio is silent, very noisy, or homogeneous, the feature matrix can have near-zero variance or NaNs/Infs. Feeding that into the SSM gives a matrix that is either constant or invalid; diagonal-line detection and period estimation then become meaningless.
- **SSM:** Even with valid features, some recordings have little repetition (e.g. free rhythm). The SSM may be almost uniform (all similarities in a narrow band). Proceeding as if there were clear structure can yield arbitrary periods and nadai.
- **Feature type:** One representation (e.g. MFCC) might not capture rhythm well for a given piece; another (e.g. tempogram or combined) might. Automatically trying an alternative when the first attempt looks bad can improve robustness without user intervention.

### What to add

1. **Flat / degenerate feature check**  
   After computing the feature matrix, check for:
   - Near-zero variance (e.g. standard deviation per feature dimension below a threshold).
   - NaNs or Infs.  
   If detected: **skip** building the SSM and raise or return a clear error/warning, **or** retry with a different `feature_type` (e.g. try `tempogram` or `combined` after `mfcc`).

2. **SSM “no structure” detection**  
   After computing the SSM, compute a simple statistic (e.g. standard deviation of the upper triangle, or range of values). If the SSM is too uniform (e.g. std below a threshold), **flag** low confidence and optionally **retry** with another feature type before continuing.

3. **Automatic feature fallback**  
   If repetition detection finds **too few** diagonal lines (e.g. below `MIN_REPETITIONS` or a configurable threshold), **re-run** Stage 1 (feature extraction) and Stage 2 (SSM) with a different `FEATURE_TYPE` (e.g. `combined` → `tempogram` → `mfcc`), then re-run Stage 3. Return the first result that has enough lines, or the best one plus a warning.

---

## 2. Potential Python libraries

| Library | Use | Documentation |
|--------|-----|----------------|
| **NumPy** | `np.nanstd`, `np.isfinite`, `np.any(np.isnan(...))` for feature checks. For SSM: `np.std(ssm)`, `np.percentile` to characterise distribution. | [NumPy](https://numpy.org/doc/stable/) |
| **SciPy** | Already used for SSM. No new functions required for this improvement. | [SciPy](https://docs.scipy.org/doc/scipy/) |
| **librosa** | Already used for features. No new APIs; the improvement is in how we validate and retry. | [librosa](https://librosa.org/doc/latest/) |

No new dependencies required.

---

## 3. Flowchart of the improvement

```mermaid
flowchart TB
    subgraph Stage1["Stage 1: Feature extraction"]
        F1[extract_features audio_path, feature_type]
        F1 --> F2[FeatureExtractor.extract]
        F2 --> F3[features matrix]
        F3 --> F4{Check: NaN/Inf?}
        F4 -->|Yes| F5[Warn; optionally retry with next feature_type]
        F4 -->|No| F6{Check: per-feature std < threshold?}
        F6 -->|Yes| F5
        F6 -->|No| F7[Return features, times]
    end

    subgraph Stage2["Stage 2: SSM"]
        S1[compute_ssm features]
        S1 --> S2[ssm matrix]
        S2 --> S3{Check: std(ssm) or range too low?}
        S3 -->|Yes| S4[Flag low_structure; optionally retry feature type]
        S3 -->|No| S5[Optionally enhance_ssm]
        S5 --> S6[Return ssm]
    end

    subgraph Fallback["Auto feature fallback"]
        A1[After find_diagonal_lines]
        A1 --> A2{len(lines) >= min_required?}
        A2 -->|No| A3[Next feature_type in list]
        A3 --> A4[Re-run extract_features + compute_ssm + find_diagonal_lines]
        A4 --> A2
        A2 -->|Yes| A5[Proceed to Stage 4]
        A2 -->|No, exhausted list| A6[Proceed with warning: few repetitions]
    end

    F7 --> S1
    F5 --> F1
    S4 --> F1
    S6 --> A1
```

**Integration points:**

- **Feature check:** In `extract_features` or at the start of `compute_ssm` in the pipeline, after obtaining `features`. Add a helper e.g. `check_feature_quality(features) -> (ok: bool, message: str)`.
- **SSM check:** In the pipeline after `compute_ssm` (and optionally after `enhance_ssm`), call e.g. `check_ssm_structure(ssm) -> (ok: bool, message: str)`. If not ok, either retry with next feature type or set a flag and continue.
- **Fallback loop:** In the pipeline, after `find_diagonal_lines`: if count is below threshold, loop over a list of feature types (from config), re-run Stages 1–3, and use the first result with enough lines or attach a warning.

---

## 4. Implementation notes for students

- Add to `config/settings.py`: `FEATURE_FALLBACK_ORDER = ['combined', 'tempogram', 'mfcc', 'chroma']`, `MIN_FEATURE_STD`, `MIN_SSM_STD` (or similar), and `MIN_DIAGONAL_LINES_FOR_FALLBACK`.
- Implement `check_feature_quality(features)` in `src/core/feature_extraction.py` or in a new `src/utils/quality.py`; call it from the pipeline before Stage 2.
- Implement `check_ssm_structure(ssm)` in `src/core/ssm_analysis.py` or in the same quality module; call it after Stage 2 in the pipeline.
- Implement the fallback loop in `src/pipeline.py`: try default feature type; if lines are too few, iterate over `FEATURE_FALLBACK_ORDER` and re-run 1–3 until sufficient lines or list exhausted. Avoid infinite loops by using a fixed list and a maximum number of retries.
- Document in the result dict or warnings when a fallback was used (e.g. `feature_type_used`, `feature_fallback_used`).
