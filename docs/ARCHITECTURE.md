# Nadai Detector — Architecture & Technical Reference

This document explains the **architecture**, **technical concepts**, and **libraries** used in the nadai-detector project so that student collaborators can understand how the system works and where to find official documentation.

---

## Table of contents

1. [Project overview](#1-project-overview)
2. [High-level architecture](#2-high-level-architecture)
3. [Technical concepts](#3-technical-concepts)
4. [Libraries and documentation](#4-libraries-and-documentation)
5. [Data flow summary](#5-data-flow-summary)

---

## 1. Project overview

**Nadai** (Carnatic music) refers to the **subdivision of the beat**: how many pulses fit in one beat (e.g. 3 = tisra, 4 = caturasra). This project **automatically detects nadai** from an audio recording by:

1. Turning the audio into a **frame-based feature representation**.
2. Building a **self-similarity matrix (SSM)** that shows how similar each moment is to every other moment.
3. Finding **repeating segments** (diagonal lines in the SSM).
4. Inferring **phrase period**, **beats per phrase**, and **subdivisions per beat** from those repetitions.
5. **Classifying** the result into a named nadai (tisra, caturasra, khanda, misra, sankirna) and value.

The pipeline is **unsupervised**: it does not need labelled data, only the audio file and config in `config/settings.py`.

---

## 2. High-level architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│  Entry: main() → NadaiDetectionPipeline.detect_and_save(audio, out_dir)  │
└─────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────┐
│  detect(audio_path)                                                      │
│  ├── Stage 0: validate_audio_file (utils)                               │
│  ├── Stage 1: extract_features (core/feature_extraction)                  │
│  ├── Stage 2: compute_ssm [+ optional enhance_ssm] (core/ssm_analysis)    │
│  ├── Stage 3: find_diagonal_lines (core/ssm_analysis)                    │
│  ├── Stage 4: analyze_repetition (core/repetition_detection)             │
│  ├── Stage 5: classify_nadai (core/nadai_classifier)                      │
│  └── Return result dict (summary + ssm, times, features, lines, etc.)   │
└─────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────┐
│  If output_dir: save JSON, visualize_complete_analysis, generate_report │
└─────────────────────────────────────────────────────────────────────────┘
```

- **Controller:** `src/pipeline.py` — runs the stages and ties everything together.
- **Core:** `src/core/` — feature extraction, SSM, repetition detection, nadai classification.
- **Utils:** `src/utils/` — audio I/O, validation.
- **Visualization:** `src/visualization/` — plots and text reports.
- **Config:** `config/settings.py` — sample rate, thresholds, feature type, nadai definitions.

---

## 3. Technical concepts

### 3.1 Audio framing and hop length

Audio is a continuous signal. We work with **short overlapping windows (frames)** so we get one feature vector per frame.

- **Sample rate** (`SAMPLE_RATE`, e.g. 22050 Hz): number of samples per second.
- **Hop length** (`HOP_LENGTH`, e.g. 512): number of samples we advance between consecutive frames. So we get a new frame every `512/22050 ≈ 0.023` seconds.
- **Frame index** → time: `time = frame_index * hop_length / sample_rate`. This is what `librosa.frames_to_time` does.

All feature extraction and SSM use the same hop length so that “one frame” means the same time step everywhere.

---

### 3.2 Feature extraction (what we feed to the SSM)

We convert each frame of audio into a **feature vector**. Similar frames get similar vectors, so the SSM can detect repetition.

- **MFCC (Mel-frequency cepstral coefficients)**  
  Compact representation of the **spectral envelope** (roughly “timbre”). We use 13 MFCCs plus **delta** (rate of change) so the SSM can use both timbre and short-term dynamics.  
  - In code: `librosa.feature.mfcc`, `librosa.feature.delta`.

- **Chroma**  
  Maps the spectrum onto **12 pitch classes** (C, C#, …, B), so the same melody in different octaves looks similar. Good for harmonic repetition.  
  - In code: `librosa.feature.chroma_cqt` (constant-Q transform based).

- **Tempogram**  
  Built from **onset strength** (how “percussive” or “attack-like” each frame is). The tempogram describes **rhythmic periodicities** (e.g. beat, half-beat). Directly targets rhythm.  
  - In code: `librosa.onset.onset_strength`, then `librosa.feature.tempogram`.

- **Combined (default)**  
  We stack **mel (dB)**, **spectral contrast**, and **onset strength** to capture timbre, spectral shape, and rhythm in one matrix. Tuned for rhythm/nadai rather than melody.

All of these are **frame-wise**: shape `(n_features, n_frames)`. We optionally **normalise** columns before building the SSM so that distance is not dominated by one feature type.

---

### 3.3 Self-similarity matrix (SSM)

The **self-similarity matrix** is a square matrix where:

- Rows and columns both index **time** (frame index or time in seconds).
- Entry `(i, j)` = **similarity** between the feature vector at time `i` and the feature vector at time `j`.

So:

- **Diagonal** `(i, i)` = similarity of a frame with itself → usually 1 (or high).
- **Off-diagonal** `(i, j)` = how much moment `i` “sounds like” moment `j`. If a phrase repeats every 10 seconds, we see **diagonal lines** parallel to the main diagonal, offset by the repetition period.

**How we build it:**

1. Take the feature matrix `(n_features, n_frames)`.
2. Optionally **normalise** each column (e.g. L2) so that we measure angle/structure, not level.
3. Transpose to `(n_frames, n_features)`.
4. Compute **pairwise distances** between all frame vectors (e.g. cosine distance via `scipy.spatial.distance.pdist`).
5. Turn distance into **similarity** (e.g. `1 - distance` for cosine so that 0 distance → 1 similarity).

**Metrics we support:** cosine, euclidean, correlation (all converted to a 0–1 similarity scale where 1 = most similar).

**Enhancement:** We optionally **smooth** the SSM with a small uniform filter (`scipy.ndimage.uniform_filter`) along rows and columns so that diagonal stripes are clearer and less noisy.

---

### 3.4 Diagonal lines and repetition

A **repeating segment** in the audio means: “the content at time `t` is similar to the content at time `t + τ`” for some **lag** `τ`. In the SSM, that shows up as high similarity along the **diagonal** line where row `i` and column `j` satisfy `j - i = τ` (constant lag).

- **Diagonal line** = a contiguous run of cells above a **similarity threshold** along a fixed lag.
- **Lag** (in frames or seconds) = **repetition period** (e.g. phrase length).
- We only keep lines longer than **min_length** (e.g. 0.5 s) so short blips don’t count as structure.

So **finding repetitions** = **finding diagonal lines** in the SSM. For each line we store start/end time, lag (period), duration, and average strength. That list is the input to “rhythm structure” analysis.

---

### 3.5 Time-lag matrix (visualisation and intuition)

The **time-lag matrix** is another view of the same information:

- **Rows** = lag (0, 1, 2, … frames).
- **Columns** = time (position along the audio).
- **Value at (lag, time)** = SSM entry `(time, time + lag)`.

So for each time we see “how strong is repetition at this lag?”. Peaks at a given lag indicate that that **lag** is a prominent period in the piece. We use this mainly for **plotting**; the actual period we use comes from clustering diagonal-line lags (see below).

---

### 3.6 Period and sub-patterns (rhythm structure)

From the list of diagonal lines we need:

- **Phrase period** (in seconds): the main repetition period.
- **Beats per phrase** and **subdivisions per beat**: so we can name the **nadai**.

**Finding the phrase period:**

- We take lag times of **strong, long enough** lines.
- **Cluster** lags that are within `PERIOD_TOLERANCE` (e.g. 0.1 s) of each other.
- The **largest cluster** is treated as the dominant period; we use its **median** as the phrase period.

**Sub-patterns:**

- We look at lines whose lag is **shorter** than the phrase period.
- If `period / lag` is close to an integer (e.g. 2, 4, 8), that lag is an **integer division** of the phrase (e.g. half-phrase, quarter-phrase).
- We keep only divisions with sufficient average strength and reasonable division count (e.g. 2–16). These are **sub-patterns**.

**Beats and subdivisions:**

- We try to explain the **total number of subdivisions** (from the largest sub-pattern) as **beats × nadai** using common Carnatic beat counts (3, 4, 5, …) and nadai bases (3, 4, 5, 7, 9). If that fails, we fall back to the smallest sub-pattern as beat level and infer or default nadai (e.g. caturasra 4).

---

### 3.7 Nadai classification

**Nadai** is the number of **subdivisions per beat** in Carnatic rhythm:

- **Tisra** — 3 (and multiples 3, 6, 12, …).
- **Caturasra** — 4 (and 2, 4, 8, 16, …).
- **Khanda** — 5.
- **Misra** — 7.
- **Sankirna** — 9.

We get a **float** “subdivisions per beat” from the structure step; we **round** it to an integer and then:

- Check **NADAI_DEFINITIONS** for an exact match in the multiples.
- Else use divisibility rules (e.g. divisible by 9 → sankirna, by 7 → misra, by 5 → khanda, by 3 and not power of 2 → tisra, power of 2 or divisible by 4 → caturasra).

So the **output** is a label (e.g. `caturasra`) and a value (e.g. `4`).

---

## 4. Libraries and documentation

Below are the **libraries used directly** in the project, what they are used for here, and links to their official technical documentation.

---

### 4.1 NumPy

- **What it is:** Fundamental library for **numerical computing** in Python: arrays, broadcasting, linear algebra, and fast element-wise operations.
- **Used for:** Storing and manipulating feature matrices, SSM, time arrays, and all numeric data; frame indices, clustering (lag arrays), and general math.
- **Docs:** [NumPy documentation](https://numpy.org/doc/stable/) (User Guide, API reference).

---

### 4.2 SciPy

- **What it is:** Scientific computing built on NumPy: statistics, optimization, signal processing, spatial algorithms, etc.
- **Used in this project:**
  - **`scipy.spatial.distance.pdist`** — Pairwise distances between rows of a matrix (we use it for frame-to-frame distance with metrics like `'cosine'`, `'euclidean'`, `'correlation'`).  
    [scipy.spatial.distance](https://docs.scipy.org/doc/scipy/reference/spatial.distance.html)
  - **`scipy.spatial.distance.squareform`** — Converts the condensed distance vector from `pdist` into a square distance matrix.  
    Same page as above.
  - **`scipy.ndimage.uniform_filter`** — Uniform (box) filter for smoothing the SSM so diagonal structure is clearer.  
    [scipy.ndimage](https://docs.scipy.org/doc/scipy/reference/ndimage.html)
- **Docs:** [SciPy documentation](https://docs.scipy.org/doc/scipy/).

---

### 4.3 librosa

- **What it is:** Library for **audio and music analysis**: loading audio, spectral representations, features (MFCC, chroma, onset, tempogram), and time/frame conversions.
- **Used in this project:**
  - **Loading audio:** `librosa.load` (with optional resampling to our `SAMPLE_RATE`).
  - **Normalisation:** `librosa.util.normalize` for feature columns before SSM.
  - **Features:** `mfcc`, `delta`, `chroma_cqt`, `onset_strength`, `tempogram`, `melspectrogram`, `power_to_db`, `spectral_contrast`.
  - **Time mapping:** `librosa.frames_to_time` (frame index → time in seconds).
- **Docs:** [librosa documentation](https://librosa.org/doc/latest/) (API and tutorials).

---

### 4.4 soundfile

- **What it is:** Thin wrapper around **libsndfile** for reading and writing audio files (WAV, FLAC, OGG, etc.) with a simple NumPy interface.
- **Used in this project:** Reading file metadata (duration, sample rate, format) via `soundfile.info` in `get_audio_info`; optionally writing output audio via `soundfile.write`. If `soundfile` fails to open a file (e.g. unsupported WAV encoding), we fall back to `librosa.load` for validation.
- **Docs:** [PySoundFile documentation](https://pysoundfile.readthedocs.io/).

---

### 4.5 matplotlib

- **What it is:** Standard Python library for **2D (and basic 3D) plotting**: figures, axes, line plots, images, colorbars, saving to file.
- **Used in this project:**
  - **`matplotlib.pyplot`** — Figure creation, subplots, `imshow` (SSM and time-lag matrices), `plot`, `savefig`, styles.
  - **`matplotlib.colors`** — `LinearSegmentedColormap.from_list` for custom colormaps (e.g. diagonal-line colour).
- **Docs:** [Matplotlib documentation](https://matplotlib.org/stable/contents.html) (User Guide and API).

---

### 4.6 Seaborn (indirect)

- **What it is:** High-level plotting library built on matplotlib, providing themes and statistical plots.
- **Used in this project:** Only via **plot style**: `plt.style.use('seaborn-v0_8-darkgrid')` in `config/settings.py` to set a default look. No direct seaborn API calls in the code.
- **Docs:** [Seaborn documentation](https://seaborn.pydata.org/).

---

### 4.7 Python standard library (brief)

- **`pathlib.Path`** — Object-oriented path handling (exists, suffix, stem, parent, etc.).
- **`json`** — Serialising the result summary to JSON for output.
- **`typing`** — Type hints (`Dict`, `List`, `Optional`, `Tuple`, `Any`) for readability and tooling.
- **`argparse`** — Parsing command-line arguments (`audio_file`, `-o`, `-q`) in `main()`.

---

## 5. Data flow summary

| Stage   | Input(s)              | Output(s)                    | Main idea                                      |
|--------|------------------------|------------------------------|------------------------------------------------|
| 0      | `audio_path`          | Valid / raise                | File exists, format supported, duration OK.    |
| 1      | `audio_path`          | `features`, `times`          | Frame-based features (mfcc/chroma/tempogram/combined). |
| 2      | `features`            | `ssm` (optionally enhanced)  | Pairwise similarity of frames.                  |
| 3      | `ssm`, `times`        | `diagonal_lines`             | Diagonal lines = repetitions (lag, strength).  |
| 4      | `diagonal_lines`, `ssm`, `times` | `period`, `num_beats`, `subdivisions_per_beat`, `sub_patterns` | Period from clusters; structure from sub-patterns. |
| 5      | `subdivisions_per_beat`| `nadai_type`, `nadai_value`  | Map to Carnatic nadai name and value.          |
| Output | `result`, `output_dir` | JSON, PNG plot, TXT report   | Serialise and visualise.                       |

---

This architecture and the linked documentation should be enough for student collaborators to follow the code, understand the concepts, and extend or debug the pipeline. For a step-by-step call graph and method-level descriptions, see [pipeline_flowchart.md](pipeline_flowchart.md).
