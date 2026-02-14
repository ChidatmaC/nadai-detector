# Improvement 1: Input and Validation

**Goal:** Make the pipeline robust to bad or marginal input by checking audio level, channel layout, and read errors before running the detection stages. Students implementing this improvement will add **silence/level checks**, **stereo-to-mono handling**, and **clearer handling of corrupt or unreadable audio**.

---

## 1. Concept

### Why it matters

The current pipeline validates that the file exists, has a supported extension, and can be read to get duration. It does **not** check:

- Whether the audio is mostly **silence** or very quiet (which leads to degenerate features and a meaningless SSM).
- Whether the file is **stereo** — we use `librosa.load`, which returns mono by default, but metadata and duration may come from `soundfile`, which can see stereo; consistency and explicit handling avoid confusion.
- **What went wrong** when reading fails — we can distinguish “file not found”, “format not recognised”, “corrupt/unreadable”, and surface a clear, actionable message.

### What to add

1. **Silence / level check**  
   After loading (or after getting duration), compute a simple measure of loudness (e.g. RMS or integrated loudness over short windows). If the signal is below a threshold (e.g. most frames have RMS < 1e-4), **reject** the file or **warn** and optionally skip processing. Optionally **trim** leading and trailing silence so the pipeline operates on the “active” part of the recording.

2. **Stereo handling**  
   When reading audio for features or metadata, **explicitly** convert stereo to mono (e.g. average the channels or take the first channel) and document this in code. Ensure both `get_audio_info` and the feature extractor use the same convention so duration and frame count are consistent.

3. **Corrupt / unreadable frames**  
   When the librosa fallback is used (after soundfile fails), **catch** read or decode errors (e.g. partial read, invalid samples). Return a **structured error** or raise with a message like “File may be corrupted or use an unsupported encoding; try re-exporting as PCM WAV or FLAC” so users know what to do.

---

## 2. Potential Python libraries

| Library | Use | Documentation |
|--------|-----|----------------|
| **librosa** | Already used. `librosa.load` returns mono by default; for stereo you get a mix. Use `librosa.to_mono(y)` if you keep stereo temporarily, or load with channel handling. RMS: `librosa.feature.rms(y=y)`. Trim: `librosa.effects.trim(y, top_db=...)` to trim silence by dB below peak. | [librosa doc](https://librosa.org/doc/latest/) |
| **soundfile** | Already used. `sf.info()` gives channels; when reading, you can read multichannel and downmix in code, or rely on librosa for loading. | [PySoundFile](https://pysoundfile.readthedocs.io/) |
| **NumPy** | Compare RMS array to threshold; `np.percentile`, `np.mean` for level stats. | [NumPy](https://numpy.org/doc/stable/) |

No new dependencies are strictly required; the above are already in the project or standard.

---

## 3. Flowchart of the improvement

```mermaid
flowchart TB
    subgraph Current["Current flow"]
        A1[validate_audio_file]
        A1 --> A2[Path exists?]
        A2 --> A3[Extension supported?]
        A3 --> A4[get_audio_info]
        A4 --> A5[Duration in range?]
    end

    subgraph New["New: input and validation"]
        B1[validate_audio_file]
        B1 --> B2[Path exists?]
        B2 --> B3[Extension supported?]
        B3 --> B4[get_audio_info]
        B4 --> B5[Duration in range?]
        B5 --> B6{Channels > 1?}
        B6 -->|Yes| B7[Ensure mono: avg channels or to_mono]
        B6 -->|No| B8[Load / get segment for level check]
        B7 --> B8
        B8 --> B9[Compute RMS or loudness per frame]
        B9 --> B10{Mean or percentile RMS < threshold?}
        B10 -->|Yes| B11[Reject or warn: "Audio too quiet or silent"]
        B10 -->|No| B12[Optional: trim leading/trailing silence]
        B12 --> B13[Proceed to Stage 1]
        B11 --> B14[Raise or return structured error]
        B4 -.->|Read error| B15[Catch exception; raise with message: re-export as PCM WAV/FLAC]
    end
```

**Integration point:** Call the new checks inside `validate_audio_file` (after duration check). Optionally, add a small helper that loads a short segment or uses duration + a single read to compute level, so validation stays fast. Trim (if implemented) can be applied in `load_audio` or at the start of feature extraction so all downstream stages see the same waveform.

---

## 4. Implementation notes for students

- Add config in `config/settings.py`: e.g. `MIN_RMS_THRESHOLD`, `TRIM_TOP_DB` (or disable trim with `None`), and `AUDIO_CHANNELS` (e.g. `'mono'` or `'first'`).
- In `src/utils/audio_io.py`: ensure `get_audio_info` and `load_audio` document and implement the same stereo→mono policy; use `librosa.to_mono` if you ever need to support stereo explicitly.
- In `src/utils/validation.py`: after `get_audio_info`, optionally load a short segment (or the full file if small) to compute RMS; if below threshold, raise a clear `ValueError` or append to a `warnings` list (see Improvement 7). When catching exceptions from `get_audio_info`, re-raise with an improved message for “format not recognised” or “corrupt” cases.
- Add unit tests: a silent WAV, a stereo WAV, and (if possible) a malformed file that triggers the fallback and the new error message.
