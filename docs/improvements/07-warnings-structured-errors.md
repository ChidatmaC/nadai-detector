# Improvement 7: Warnings and Structured Errors

**Goal:** Introduce a **warnings** list in the pipeline result and **structured error types** so that callers (and the report generator) can show what went wrong or what was fallback without failing the whole run. Students implementing this improvement will add a **result['warnings']** list and optional **custom exception types** for validation and pipeline stages.

---

## 1. Concept

### Why it matters

- **Warnings:** Many robustness improvements (1–6) add **flags** or **fallbacks** (e.g. “period from fallback”, “unknown nadai”, “few repetitions”). Instead of only storing boolean flags, a single **list of warning messages** (e.g. `["Audio level low", "Period from fallback", "Nadai from nearest match"]`) gives a clear, human-readable summary and can be rendered in reports and UIs without interpreting many keys.
- **Structured errors:** When validation fails (e.g. file not found, format not recognised, too quiet), raising a **custom exception** (e.g. `ValidationError` with a `code` and `message`) allows the CLI or API to map to exit codes or HTTP status and to display consistent messages. Same for “no repetitions” or “could not determine period” so the pipeline can distinguish **recoverable** vs **fatal** cases if you add retry at a higher level.

### What to add

1. **Result warnings list**  
   Initialise `result['warnings'] = []` at the start of `detect()`. In every stage where a fallback or a quality issue is detected, **append** a short string (e.g. `"Audio level below threshold; result may be unreliable"`, `"Period from fallback (no strong cluster)"`, `"Few diagonal lines; structure may be uncertain"`). Ensure the list is always present and serialised in the JSON output (and optionally in the text report).

2. **Structured error types**  
   Define a small hierarchy (e.g. `NadaiDetectorError` base, `ValidationError`, `NoRepetitionsError`, `PeriodDetectionError`) with attributes such as `message` and `code` (e.g. `FILE_NOT_FOUND`, `FORMAT_NOT_RECOGNISED`, `NO_REPETITIONS`). In `validate_audio_file` and in the pipeline where we currently raise `ValueError`, raise these instead. The `main()` CLI can catch them and print `message` and exit with a non-zero code; the report can mention “Validation failed: FILE_NOT_FOUND”.

3. **Report integration**  
   In `generate_report` (and in the report template), add a **Warnings** section: if `result.get('warnings')` is non-empty, list each warning. For failed runs that return a structured error, the report (or a separate error report) can show `error.code` and `error.message`.

---

## 2. Potential Python libraries

| Library | Use | Documentation |
|--------|-----|----------------|
| **Standard library** | Define custom exceptions by subclassing `Exception`; no extra deps. | [Python docs — Exceptions](https://docs.python.org/3/tutorial/errors.html) |

No new dependencies.

---

## 3. Flowchart of the improvement

```mermaid
flowchart TB
    subgraph Init["Start detect()"]
        I1[result = {}]
        I1 --> I2[result['warnings'] = []]
    end

    subgraph Stages["During stages"]
        S1[Stage 0: if quiet/silent → append warning]
        S2[Stage 1–2: if feature/SSM fallback → append]
        S3[Stage 3: if few lines or relaxed → append]
        S4[Stage 4: if period/structure fallback → append]
        S5[Stage 5: if nadai fallback → append]
        S6[Sanity: if bounds violated → append]
    end

    subgraph Errors["Structured errors"]
        E1[ValidationError]
        E1 --> E2[FILE_NOT_FOUND]
        E1 --> E3[FORMAT_NOT_RECOGNISED]
        E1 --> E4[AUDIO_TOO_QUIET]
        E5[NoRepetitionsError]
        E6[PeriodDetectionError]
    end

    subgraph Output["Output"]
        O1[JSON: include result['warnings']]
        O2[Report: Warnings section if non-empty]
        O3[CLI: catch NadaiDetectorError → print message, exit code]
    end

    I2 --> S1
    S1 --> S2 --> S3 --> S4 --> S5 --> S6
    S6 --> O1
    E1 --> O3
    E5 --> O3
    E6 --> O3
    O1 --> O2
```

**Integration points:**

- **Warnings:** In `src/pipeline.py`, at the top of `detect()`, set `result['warnings'] = []`. After each stage (or inside helpers called from the pipeline), when you detect a fallback or issue, append a string to `result['warnings']`. When building the final result dict, include `'warnings': result['warnings']`. In `generate_report`, if `result.get('warnings')`: add a “Warnings” section and iterate over the list.
- **Exceptions:** Create a new module e.g. `src/utils/exceptions.py` with `class NadaiDetectorError(Exception)`, `class ValidationError(NadaiDetectorError)`, etc. Give each a `code` (string) and use `super().__init__(message)`. In `validate_audio_file`, raise `ValidationError("...", code="FILE_NOT_FOUND")` instead of `ValueError`. In the pipeline, where you raise “No repetitions” or “Could not determine period”, raise `NoRepetitionsError` or `PeriodDetectionError`. In `main()`, catch `NadaiDetectorError` (or the base), print `e.message`, and `sys.exit(2)` or a chosen code.
- **JSON:** Ensure the summary you dump to JSON (the one that excludes large arrays) includes `warnings` so that API or UI consumers can show them.

---

## 4. Implementation notes for students

- **Backward compatibility:** If existing code catches `ValueError`, you can make `ValidationError` inherit from both `NadaiDetectorError` and `ValueError`, or document that callers should catch `NadaiDetectorError` for structured handling.
- **i18n:** Keep warning and error messages in English in code; they can be mapped to locale-specific strings in a UI layer later.
- **Codes:** Use UPPER_SNAKE_CASE for codes (e.g. `PERIOD_FROM_FALLBACK`, `NADAI_NEAREST_FALLBACK`) so they are stable for programmatic use.
