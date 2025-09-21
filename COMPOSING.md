# Composing Guide (Tart)

This guide shows how to quickly author Strudel tracks, iterate with targeted renders, and assemble longer songs using the Tart toolchain.

## TL;DR Flow

1) Scaffold a track

```bash
~/.local/bin/uv run strudel-orchestrator init neon-impulse --tempo 170
```

2) Author the pattern in `tracks/<slug>.strudel` (YAML front matter + Strudel code). Keep parts named (`const drums`, `const bass`, `const vox`, etc.).

3) Validate fast

```bash
~/.local/bin/uv run strudel-orchestrator compile --check-only
```

4) Render WAV(s) for quick listening

```bash
~/.local/bin/uv run strudel-orchestrator render \
  --slug neon-impulse --format wav --warmup 4 --duration 8
```

5) Batch render variants into folders (and rotate old audio)

```bash
~/.local/bin/uv run strudel-orchestrator render-suite \
  --slug neon-impulse \
  --variants "" \
  --variants "hush(); vox.gain(0.4)" \
  --variants "hush(); drums.gain(0.9)" \
  --rotate --format wav --warmup 4 --duration 8
```

6) Splice/loop WAVs to shape sections

```bash
~/.local/bin/uv run strudel-orchestrator splice \
  --inputs audio/neon-impulse/v00/neon-impulse.wav \
  --inputs audio/neon-impulse/v01/neon-impulse.wav \
  --inputs audio/neon-impulse/v02/neon-impulse.wav \
  --out audio/neon-impulse/neon-impulse-suite.wav

~/.local/bin/uv run strudel-orchestrator loop \
  --input audio/neon-impulse/v02/neon-impulse.wav \
  --repeats 4 \
  --out audio/neon-impulse/neon-impulse-build.wav
```

## Available Tools

- init: create new `tracks/<slug>.strudel` with YAML metadata + starter pattern.
- compile: validate metadata and pattern; emit artifacts in `dist/` (json/md/raw) unless `--check-only`.
- render: bounce to audio with Playwright (default WAV-only).
  - Flags: `--slug`, `--warmup`, `--duration`, `--format wav`, `--play-expr`.
- render-suite: render multiple variants and rotate `audio/` to `audio_OLD/`.
  - Flags: `--slug` (repeatable), `--variants` (repeatable), `--formats wav`, `--warmup`, `--duration`, `--rotate`.
- splice: concatenate WAVs (ffmpeg concat demuxer).
- loop: repeat a WAV N times (ffmpeg filter_complex concat).
- fetch-strudel: shallow sparse-clone upstream Strudel repo into `vendor/strudel` for reference.

Requirements: `~/.local/bin/uv` for Python deps; Playwright Chromium (`uv run playwright install chromium` once); `ffmpeg` in PATH for audio conversion/splicing.

## Efficient Prompting Patterns

Use these compact prompts with the assistant for faster iteration:

- New DnB track
  - “Create a new DnB track named <slug> at 170 CPM (quarter math), with parts: drums (kick 0,7?,10; snare 4,12; eighth hats), bass supersaw in F minor with ducking, vox chops using scrub+rib, and a pulse/FM riser. Render base WAV for 8s.”

- Variation set
  - “Render three variants for <slug>: base; vox light; drums emphasized. Use `--play-expr` expressions and `render-suite`, then list the output folders.”

- Arrangement assembly
  - “Splice v00, v01, v02 into a suite WAV and loop v02 four times as a build. Output under `audio/<slug>/`.”

- Safety/style checks
  - “Ensure all `.gain()` ≤ 1.0, use `orbit` separation for drums vs long tails, and kick-based `duck` for headroom. Re-render the base after applying.”

Keep context short and actionable; specify slugs, durations, and desired variations.

## Composing: From Sketch to Song

1) Clock & tempo

- Use quarter-note math for DnB: `setcpm(170/4)`.
- For other genres, set `setcpm(x)` or `setcps(y)` once at the top.

2) Parts & naming

- Define parts as constants so they’re addressable:
  - `const drums = ... .orbit(2)`
  - `const bass = ... .orbit(3)`
  - `const vox = ... .orbit(4)`
  - `const riser = ... .orbit(5)`
- Keep names stable; these can be referenced in variant expressions appended via `--play-expr`, e.g., `hush(); drums.gain(0.9)`.

3) Rhythm & placement

- Drums: `beat("0,7?,10",16)` for DnB kicks; `beat("4,12",16)` for snares; hats via `s("hh:4!8")`.
- Bass: pick a mode/scale (e.g., F minor), use `.note(...)` and `.sub(12)`.

4) Tone shaping & headroom

- Use `lpf(value)`, `lpenv(shape)`, and modulation (`rand`, `seg`) for motion.
- Route long tails to separate `orbit`s; sidechain with `duck("<orbits>")` on the kick.
- Keep any `.gain()` ≤ 1.0 to avoid clipping.

5) Arrangement

- Start with a simple `stack(parts...)`.
- For “build” or “breakdown” renders, use `--play-expr` variants that hush and bring up a subset: `hush(); vox.gain(0.4)`.
- Use `render-suite` to generate multiple section WAVs in one go.

6) Assembly & polish

- Splice sections into a longer WAV, then loop builds or intros as needed.
- Optional: run an external loudness pass (e.g., ffmpeg `loudnorm`) if targeting consistent LUFS.

## Project Structure & Outputs

- tracks/<slug>.strudel: sources (YAML + Strudel).
- dist/: compiled artifacts (json, md, raw) from `compile`.
- audio/: WAV export root.
  - audio/<slug>/v00|v01|...: per-variant WAVs from `render-suite`.
  - audio_OLD/: rotated archive when `--rotate` is used.

## Troubleshooting

- Missing audio on first trigger: samples may be downloading—re-render or extend warmup.
- ffmpeg errors: ensure ffmpeg is installed and inputs exist.
- Playwright errors: run `~/.local/bin/uv run playwright install chromium`.
- Lint failures: check `assets/strudel_linter.html` exists; see `logs/` for details.

## Checklists

Before commit:

- `compile --check-only` returns 0
- `pytest` passes
- Short `render --format wav` smoke works

Before release:

- Render suite variants
- Splice final arrangement
- Verify headroom and tails
