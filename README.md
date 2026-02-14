# Nadai Detector

Automated **nadai** (beat subdivision) detection for Carnatic rhythm from audio, using self-similarity matrices (SSM) and repetition analysis.

---

## Documentation

- **[Pipeline flowchart & method descriptions](docs/pipeline_flowchart.md)** — Mermaid diagram of the main controller and all callees, plus short explanations of what each method does.
- **[Architecture & technical reference](docs/ARCHITECTURE.md)** — Project architecture, technical concepts (SSM, features, diagonal lines, nadai), libraries used with links to their official docs, and a data-flow summary for collaborators.

---

## Quick start

```bash
# From project root, with your environment activated (e.g. conda)
pip install -r requirements.txt
python src/pipeline.py path/to/audio.wav -o data/output
```

**Supported audio:** `.wav`, `.mp3`, `.flac`, `.ogg`, `.aiff` (duration 2 s–10 min).

**Options:** `-o` / `--output` — output directory (default: `data/output`). `-q` / `--quiet` — minimal logging.

---

## Output

When an output directory is given, the pipeline can write:

- **JSON** — `output_dir/json/<stem>_result.json` (summary only).
- **Plot** — `output_dir/plots/<stem>_analysis.png` (SSM, time-lag, sub-patterns, summary).
- **Report** — `output_dir/reports/<stem>_report.txt` (text report).

Enable/disable in `config/settings.py` (`OUTPUT_JSON`, `OUTPUT_PLOT`, `OUTPUT_REPORT`).
