# Nadai Detector — Robustness Improvements

This document is an **index** of proposed improvements for error detection and self-correction. Each improvement is described in its own file so that **student collaborators can implement them independently**. Each file includes:

- A **thorough explanation** of the concept and why it helps
- **Potential Python libraries** to use
- A **Mermaid flowchart** of how the improvement fits into the pipeline

---

## Improvement documents

| # | Topic | File | Summary |
|---|--------|------|--------|
| 1 | **Input and validation** | [01-input-validation.md](improvements/01-input-validation.md) | Silence/level checks, stereo→mono handling, clearer handling of corrupt or unreadable audio |
| 2 | **Feature and SSM quality** | [02-feature-ssm-quality.md](improvements/02-feature-ssm-quality.md) | Detecting flat or degenerate features, SSM with no structure, automatic feature-type fallback |
| 3 | **Repetition detection robustness** | [03-repetition-detection.md](improvements/03-repetition-detection.md) | Handling too few or too many diagonal lines, conflicting period clusters |
| 4 | **Rhythm structure robustness** | [04-rhythm-structure.md](improvements/04-rhythm-structure.md) | When no period or sub-patterns are found, sanity bounds on beat duration and phrase period |
| 5 | **Nadai classification robustness** | [05-nadai-classification.md](improvements/05-nadai-classification.md) | Handling “unknown” nadai, confidence score from distance to known definitions |
| 6 | **End-to-end confidence and retry** | [06-end-to-end-confidence-retry.md](improvements/06-end-to-end-confidence-retry.md) | Pipeline-level confidence score, automatic retry with alternative config when confidence is low |
| 7 | **Warnings and structured errors** | [07-warnings-structured-errors.md](improvements/07-warnings-structured-errors.md) | A `warnings` list in the result and structured error types for callers and reports |

---

## Suggested implementation order

For students picking tasks:

1. **Start with 1 (input/validation)** and **7 (warnings)** — they are self-contained and improve UX immediately.
2. **Then 4 (rhythm structure)** and **5 (nadai)** — add sanity checks and confidence without changing the main control flow.
3. **Then 2 (feature/SSM)** and **3 (repetition)** — add quality checks and optional retries inside stages.
4. **Finally 6 (end-to-end)** — tie everything together with a global confidence score and config retry.

---

## Where to plug into the codebase

| Improvement | Main files to modify |
|-------------|----------------------|
| 1. Input and validation | `src/utils/validation.py`, `src/utils/audio_io.py` |
| 2. Feature and SSM quality | `src/core/feature_extraction.py`, `src/core/ssm_analysis.py`, `src/pipeline.py` |
| 3. Repetition detection | `src/core/ssm_analysis.py`, `src/core/repetition_detection.py`, `src/pipeline.py` |
| 4. Rhythm structure | `src/core/repetition_detection.py`, `config/settings.py` |
| 5. Nadai classification | `src/core/nadai_classifier.py`, `src/pipeline.py` |
| 6. End-to-end confidence and retry | `src/pipeline.py`, `config/settings.py` |
| 7. Warnings and structured errors | `src/pipeline.py`, `src/utils/validation.py`, `src/visualization/reports.py` |

See the individual improvement files for detailed flowcharts and implementation notes.
