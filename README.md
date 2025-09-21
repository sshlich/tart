# Strudel Orchestrator

Agent-oriented toolkit for authoring and compiling Strudel live-coding tracks. The CLI, implemented in Python, validates YAML-front-matter metadata, lints Strudel syntax in a headless browser, runs structural checks on the pattern code, exports ready-to-share artifacts, and can bounce patterns to audio (WebM/WAV/MP3) via Playwright-driven rendering. Use `uv` to manage dependencies and run the `strudel-orchestrator` command-line interface.

## Quick Start

```bash
~/.local/bin/uv sync
~/.local/bin/uv run playwright install chromium  # one-time browser download
~/.local/bin/uv run strudel-orchestrator compile
~/.local/bin/uv run strudel-orchestrator render --format wav,mp3 --warmup 4 --duration 8
```

Audio exports appear under `audio/` by default; compilation artifacts remain in `dist/`. The renderer currently normalises `.bank("RolandTR…")` calls to the core kit equivalents so every pattern has an audible fallback even if a specialised sample pack is unavailable.

See `AGENTS.md` for the end-to-end workflow and role definitions.
