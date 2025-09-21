# Repository Guidelines

## Project Structure & Module Organization
- `src/strudel_orchestrator/` contains the Python CLI: `cli.py` handles args, `orchestrator.py` runs compilation, `renderer.py` exports audio, and shared helpers live alongside.
- Author Strudel sources in `tracks/`; filenames use kebab-case and mirror the `slug` in the metadata front matter.
- Generated outputs land in `dist/` (JSON/Markdown/raw) and `audio/`; `logs/` stores timestamped run reports. Delete or ignore regenerated folders before committing.
- Reference docs (`STRUDEL-README.md`, `STRUDEL-LIBRARY.md`, HTML primers) sit at the repo root for quick lookup.

## Build, Test, and Development Commands
- `~/.local/bin/uv sync` installs locked dependencies for Python 3.11+.
- `~/.local/bin/uv run strudel-orchestrator init <slug>` scaffolds a new `tracks/<slug>.strudel`.
- `~/.local/bin/uv run strudel-orchestrator compile --check-only` performs metadata + syntax validation without touching `dist/`.
- `~/.local/bin/uv run strudel-orchestrator compile` writes distributable artifacts and summary logs.
- `~/.local/bin/uv run strudel-orchestrator render --format wav,mp3 --warmup 4 --duration 8` captures audio (run `uv run playwright install chromium` once beforehand).

## Coding Style & Naming Conventions
- Follow PEP 8 with 4-space indentation; prefer descriptive module-level functions and keep CLI-visible code documented. Add type hints for new helpers.
- Use the structured logger provided in `logger.py`; avoid ad-hoc `print`.
- Track files start with YAML front matter (`slug`, `title`, `tempo`, `mood`, `tags`, `summary`, optional `resources`) and a single top-level `setcpm`/`setcps`. Keep constants named after their musical role (`const chords`, `const bassLine`).
- Gains stay ≤ 1.0; note any external sample packs in `resources` for reproducibility.

## Testing Guidelines
- Treat `compile --check-only` as the fast gate before commits; it flags missing metadata, invalid tags, and pattern syntax errors.
- Run full `compile` when adjusting orchestrator logic or introducing new tracks; inspect the emitted `logs/<timestamp>.log` for warnings.
- If you add Python logic, create focussed `pytest` cases (mirroring the module path) under a `tests/` folder and execute them via `~/.local/bin/uv run pytest`.

## Commit & Pull Request Guidelines
- Use concise, imperative commit subjects (`Add stack gain guard`) and reserve bodies for rationale or links.
- Ensure generated assets are either regenerated in CI or excluded from the diff; never commit transient `logs/` or local audio experiments.
- Pull requests should explain intent, list affected tracks/modules, confirm validation commands run, and attach rendered audio when relevant.
- Reference related issues or task IDs and call out follow-up work so reviewers can hand off confidently.
