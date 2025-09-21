"""Playwright-backed Strudel syntax linter."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, TYPE_CHECKING

from playwright.async_api import async_playwright, Page, Playwright

from .logger import Logger

if TYPE_CHECKING:
    from .orchestrator import TrackArtifact


@dataclass(slots=True)
class LintResult:
    ok: bool
    message: str | None = None


class StrudelLinter:
    """Manage a headless browser session to validate Strudel code."""

    def __init__(self, html_template: Path, logger: Logger) -> None:
        self._html_template = html_template
        self._logger = logger
        self._playwright: Playwright | None = None
        self._page: Page | None = None

    async def __aenter__(self) -> "StrudelLinter":
        try:
            self._playwright = await async_playwright().start()
        except Exception as exc:  # pragma: no cover - startup failure
            raise RuntimeError(
                "Failed to start Playwright. Did you run `uv run playwright install chromium`?"
            ) from exc
        browser = await self._playwright.chromium.launch(headless=True, args=["--autoplay-policy=no-user-gesture-required"])
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

    async def lint(self, code: str) -> LintResult:
        if not self._page:
            raise RuntimeError("Linter not initialized")
        result = await self._page.evaluate(
            "code => lintStrudel(code)",
            code,
        )
        if result.get("ok"):
            return LintResult(True, None)
        return LintResult(False, result.get("error") or "Unknown lint error")


def lint_tracks(artifacts: Iterable["TrackArtifact"], logger: Logger) -> Dict[Path, str]:
    """Lint the supplied artifacts; return mapping of failing paths to error messages."""

    root_dir = Path(__file__).resolve().parents[2]
    html_template = (root_dir / "assets" / "strudel_linter.html").resolve()
    if not html_template.exists():
        raise FileNotFoundError(f"Linter HTML template missing at {html_template}")

    artifacts = [artifact for artifact in artifacts if artifact.code]
    if not artifacts:
        return {}

    async def _lint_all() -> Dict[Path, str]:
        failures: Dict[Path, str] = {}
        async with StrudelLinter(html_template, logger) as linter:
            for artifact in artifacts:
                try:
                    result = await linter.lint(artifact.code or "")
                except Exception as exc:  # pragma: no cover - unexpected
                    failures[artifact.path] = str(exc)
                    continue
                if not result.ok:
                    failures[artifact.path] = result.message or "Unknown lint error"
        return failures

    return asyncio.run(_lint_all())


__all__ = ["lint_tracks"]
