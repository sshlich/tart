"""Playwright-powered Strudel audio renderer."""

from __future__ import annotations

import asyncio
import base64
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import List, Sequence

from playwright.async_api import async_playwright, Page, Playwright

from .logger import Logger
from .orchestrator import TrackArtifact, load_track


@dataclass(slots=True)
class RenderOptions:
    tracks_dir: Path
    out_dir: Path
    formats: Sequence[str]
    duration_ms: int
    warmup_ms: int
    slugs: Sequence[str]
    play_expr: str | None = None


class StrudelAudioRenderer:
    """Thin wrapper around Playwright to bounce Strudel patterns to audio."""

    def __init__(self, html_template: Path, logger: Logger) -> None:
        self._html_template = html_template
        self._logger = logger
        self._playwright: Playwright | None = None
        self._page: Page | None = None

    async def __aenter__(self) -> "StrudelAudioRenderer":
        try:
            self._playwright = await async_playwright().start()
        except Exception as exc:  # pragma: no cover - startup failure
            raise RuntimeError("Failed to start Playwright. Did you install it via `uv run playwright install chromium`?") from exc
        browser = await self._playwright.chromium.launch(
            headless=True,
            args=["--autoplay-policy=no-user-gesture-required"],
        )
        page = await browser.new_page()
        await page.goto(self._html_template.as_uri())
        await page.wait_for_function("window.strudelReady === true")
        self._page = page
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:
        if self._page:
            await self._page.context.close()
            self._page = None
        if self._playwright:
            await self._playwright.stop()
            self._playwright = None

    async def render(self, code: str, duration_ms: int, warmup_ms: int) -> bytes:
        if not self._page:
            raise RuntimeError("Renderer not initialized")
        result = await self._page.evaluate(
            "params => renderStrudel(params.code, { durationMs: params.durationMs, warmupMs: params.warmupMs })",
            {
                "code": code,
                "durationMs": duration_ms,
                "warmupMs": warmup_ms,
            },
        )
        base64_audio = result["base64"]
        return base64.b64decode(base64_audio)


def render_tracks(options: RenderOptions, logger: Logger) -> int:
    html_template = (options.tracks_dir.parent / "assets" / "strudel_renderer.html").resolve()
    if not html_template.exists():
        raise FileNotFoundError(f"Renderer HTML template missing at {html_template}")

    wanted_slugs = {slug.strip() for slug in options.slugs if slug.strip()}

    track_files = sorted(options.tracks_dir.glob("*.strudel"))
    if not track_files:
        logger.warn("No .strudel tracks found for rendering.")
        return 0

    artifacts: List[TrackArtifact] = []
    for path in track_files:
        artifact = load_track(path)
        if wanted_slugs and artifact.slug not in wanted_slugs:
            continue
        if artifact.errors:
            logger.error(
                "Track contains validation errors; skipping audio render",
                {"path": str(path), "errors": artifact.errors},
            )
            continue
        if artifact.warnings:
            logger.warn(
                "Track has validation warnings",
                {"path": str(path), "warnings": artifact.warnings},
            )
        if not artifact.code:
            logger.warn("Track has no pattern body; skipping", {"path": str(path)})
            continue
        artifacts.append(artifact)

    if not artifacts:
        logger.warn("No eligible tracks to render.")
        return 0

    options.out_dir.mkdir(parents=True, exist_ok=True)

    async def _render_all() -> int:
        total = 0
        async with StrudelAudioRenderer(html_template, logger) as renderer:
            for artifact in artifacts:
                logger.info(
                    "Rendering audio",
                    {"slug": artifact.slug, "duration_ms": options.duration_ms},
                )
                code_to_play = (artifact.code or "")
                if options.play_expr:
                    code_to_play = f"{code_to_play}\n{options.play_expr}\n"
                audio_bytes = await renderer.render(code_to_play, options.duration_ms, options.warmup_ms)
                webm_path = options.out_dir / f"{artifact.slug}.webm"
                webm_path.write_bytes(audio_bytes)

                convert_formats(webm_path, options.formats, logger)
                total += 1
        return total

    total_tracks = asyncio.run(_render_all())
    logger.info("Rendered tracks", {"count": total_tracks})
    return total_tracks


def convert_formats(webm_path: Path, formats: Sequence[str], logger: Logger) -> None:
    available = {fmt.strip().lower() for fmt in formats}
    # Always exclude webm from conversion target; we'll also remove the source after conversions
    if "webm" in available:
        available.remove("webm")

    for fmt in available:
        if fmt not in {"wav"}:
            logger.warn("Unsupported audio format requested; skipping", {"format": fmt})
            continue
        output_path = webm_path.with_suffix(f".{fmt}")
        command = [
            "ffmpeg",
            "-y",
            "-i",
            str(webm_path),
            str(output_path),
        ]
        if fmt == "mp3":
            command.extend(["-codec:a", "libmp3lame", "-qscale:a", "2"])
        try:
            subprocess.run(command, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        except FileNotFoundError as exc:  # pragma: no cover - environment specific
            logger.error("ffmpeg is required to convert audio formats", {"command": command})
            raise
        except subprocess.CalledProcessError as exc:
            logger.error(
                "ffmpeg failed to convert audio",
                {"command": command, "stderr": exc.stderr.decode(errors="ignore")},
            )
            raise
    # Clean up the intermediate webm source to keep audio folder WAV-only
    try:
        webm_path.unlink(missing_ok=True)
    except Exception:
        pass


__all__ = [
    "RenderOptions",
    "StrudelAudioRenderer",
    "render_tracks",
]
