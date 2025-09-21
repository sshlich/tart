# Strudel Orchestrator

Agent-oriented toolkit for authoring and compiling Strudel live-coding tracks. The CLI, implemented in Python, validates YAML-front-matter metadata, lints Strudel syntax in a headless browser, runs structural checks on the pattern code, exports ready-to-share artifacts, and can bounce patterns to audio (WebM/WAV/MP3) via Playwright-driven rendering. Use `uv` to manage dependencies and run the `strudel-orchestrator` command-line interface.

## Quick Start

```bash
~/.local/bin/uv sync
~/.local/bin/uv run playwright install chromium  # one-time browser download
~/.local/bin/uv run strudel-orchestrator compile
~/.local/bin/uv run strudel-orchestrator render --format wav --warmup 4 --duration 8
```

Audio exports appear under `audio/` by default; compilation artifacts remain in `dist/`. The renderer currently normalises `.bank("RolandTR…")` calls to the core kit equivalents so every pattern has an audible fallback even if a specialised sample pack is unavailable.

See `AGENTS.md` for the end-to-end workflow and role definitions.

## Variations, Suites, and Splicing

### Render variations with `--play-expr`

You can append a short Strudel expression after a track’s code to quickly render focused sections/variants.

Examples:

```bash
# Base pattern only
~/.local/bin/uv run strudel-orchestrator render \
  --slug neon-impulse --format wav,mp3 --warmup 4 --duration 8

# Emphasise drums only
~/.local/bin/uv run strudel-orchestrator render \
  --slug neon-impulse --play-expr "hush(); drums.gain(0.9)" \
  --format wav,mp3 --warmup 4 --duration 8

# Vox‑light variant
~/.local/bin/uv run strudel-orchestrator render \
  --slug neon-impulse --play-expr "hush(); vox.gain(0.4)" \
  --format wav,mp3 --warmup 4 --duration 8
```

The expression is concatenated after the track’s body. Use `hush()` to clear the scheduler, then call any top‑level part names you defined (e.g., `drums`, `bass`, `vox`, `riser`).

### Render a suite of variants with folder rotation

Use `render-suite` to generate multiple variants into structured folders and rotate the `audio/` directory to `audio_OLD/` first:

```bash
~/.local/bin/uv run strudel-orchestrator render-suite \
  --slug neon-impulse \
  --variants "" \
  --variants "hush(); vox.gain(0.4)" \
  --variants "hush(); drums.gain(0.9)" \
  --rotate --duration 8 --warmup 4
```

Output layout:

- `audio/<slug>/v00|v01|v02/...` each containing `.webm`, `.wav`, `.mp3`
- previous `audio/` is moved to `audio_OLD/` (if `--rotate` is passed)

Flags:

- `--variants` (repeatable): list of appended Strudel expressions; an empty string renders the base track
- `--slug` (repeatable): one or more track slugs to render
- `--duration` / `--warmup`: seconds after/before capture
- `--formats`: `wav` (renderer cleans up intermediates; audio folder remains WAV-only)

### Splicing and looping (ffmpeg)

For building longer arrangements from rendered parts, use the splicer helpers:

Python API:

```python
from pathlib import Path
from strudel_orchestrator.splicer import concat_audio, loop_audio

# Concatenate parts in order
concat_audio(
    [Path("audio/neon-impulse/v00/neon-impulse.wav"),
     Path("audio/neon-impulse/v01/neon-impulse.wav"),
     Path("audio/neon-impulse/v02/neon-impulse.wav")],
    Path("audio/neon-impulse/neon-impulse-suite.wav"),
)

# Loop a section 4 times
loop_audio(
    Path("audio/neon-impulse/v02/neon-impulse.wav"),
    repeats=4,
    output=Path("audio/neon-impulse/neon-impulse-build.wav"),
)
```

CLI wrappers:

```bash
# Concatenate inputs into one file
~/.local/bin/uv run strudel-orchestrator splice \
  --inputs audio/neon-impulse/v00/neon-impulse.wav \
  --inputs audio/neon-impulse/v01/neon-impulse.wav \
  --inputs audio/neon-impulse/v02/neon-impulse.wav \
  --out audio/neon-impulse/neon-impulse-suite.wav

# Loop a section 4 times
~/.local/bin/uv run strudel-orchestrator loop \
  --input audio/neon-impulse/v02/neon-impulse.wav \
  --repeats 4 \
  --out audio/neon-impulse/neon-impulse-build.wav
```

Notes:

- Requires `ffmpeg` in your `PATH`.
- Concat uses the demuxer (`-f concat -safe 0`), and loop uses a `filter_complex concat` graph.

