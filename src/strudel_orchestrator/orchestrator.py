"""Compilation pipeline for Strudel track sources."""

from __future__ import annotations

import json
import textwrap
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Iterable, List, Sequence, Set

import yaml

from .logger import Logger, LoggerConfig
from .schema import validate_metadata, validate_pattern_code, SLUG_PATTERN
from .linter import lint_tracks

SUPPORTED_FORMATS = {"json", "md", "raw"}


@dataclass(slots=True)
class CompilationSettings:
    tracks_dir: Path
    out_dir: Path
    formats: Set[str]
    check_only: bool
    log_dir: Path
    log_level: str


@dataclass(slots=True)
class TrackArtifact:
    path: Path
    raw_content: str
    metadata: dict | None
    code: str | None
    errors: List[str]
    warnings: List[str]
    lint_error: str | None = None

    @property
    def slug(self) -> str | None:
        if isinstance(self.metadata, dict):
            slug = self.metadata.get("slug")
            if isinstance(slug, str):
                return slug
        return None


def create_track_stub(
    slug: str,
    *,
    title: str | None,
    tempo: int,
    tracks_dir: Path,
    force: bool = False,
) -> Path:
    if not SLUG_PATTERN.match(slug):
        raise ValueError(
            "Slug must be kebab-case (lowercase alphanumerics separated by dashes)."
        )

    if title is None:
        title = slug.replace("-", " ").title()

    tracks_dir.mkdir(parents=True, exist_ok=True)
    target_path = tracks_dir / f"{slug}.strudel"

    if target_path.exists() and not force:
        raise FileExistsError(f"Track {target_path} already exists; use --force to overwrite.")

    template = textwrap.dedent(
        f"""\
        ---
        slug: {slug}
        title: "{title}"
        tempo: {tempo}
        mood: ""
        tags: []
        summary: |
          Describe the arrangement, instrumentation, and intended mood.
        resources: []
        ---
        setcpm({tempo})
        // Define shared resources (e.g., chords) here
        stack(
          sound("bd hh sd hh").bank("RolandTR707").gain(0.8),
          sound("hh*16").gain("[0.4 1]*4"),
          n("<0 [2 4] 5>").scale("C:minor").sound("sawtooth")
        )
        """
    ).strip()

    target_path.write_text(template + "\n", encoding="utf-8")
    return target_path


def compile_project(settings: CompilationSettings) -> int:
    tracks_dir = settings.tracks_dir
    logger = Logger(
        LoggerConfig(
            level=settings.log_level,
            log_file=_prepare_log_file(settings.log_dir),
        )
    )

    try:
        logger.info(
            "Starting compilation",
            {
                "tracks_dir": str(tracks_dir),
                "formats": sorted(settings.formats),
                "check_only": settings.check_only,
            },
        )

        track_paths = sorted(tracks_dir.glob("*.strudel"))
        if not track_paths:
            logger.warn("No .strudel files discovered.")

        artifacts: List[TrackArtifact] = []
        fatal_tracks: List[str] = []
        for path in track_paths:
            artifact = load_track(path, logger)
            artifacts.append(artifact)
            if artifact.errors:
                fatal_tracks.append(str(path))
            elif artifact.warnings:
                # warnings were already emitted by load_track, just track counts
                pass

        if fatal_tracks:
            logger.error(
                "Compilation aborted due to validation errors",
                {"failed_tracks": fatal_tracks},
            )
            _emit_report(logger, artifacts, success=False)
            return 1

        try:
            lint_failures = lint_tracks(artifacts, logger)
        except FileNotFoundError as exc:
            logger.error("Linter asset missing", {"error": str(exc)})
            _emit_report(logger, artifacts, success=False)
            return 1
        except RuntimeError as exc:
            logger.error(str(exc))
            _emit_report(logger, artifacts, success=False)
            return 1

        if lint_failures:
            failed_paths: List[str] = []
            for artifact in artifacts:
                failure = lint_failures.get(artifact.path)
                if failure:
                    artifact.lint_error = failure
                    artifact.errors.append(f"Lint failed: {failure}")
                    failed_paths.append(str(artifact.path))
            logger.error(
                "Compilation aborted due to lint errors",
                {"failed_tracks": failed_paths},
            )
            _emit_report(logger, artifacts, success=False)
            return 1

        if not settings.check_only:
            _write_outputs(artifacts, settings.out_dir, settings.formats, logger)
        else:
            logger.info("Check-only mode: outputs not written.")

        _emit_report(logger, artifacts, success=True)
        logger.info(
            "Compilation complete",
            {
                "tracks": len(artifacts),
                "warnings": sum(bool(a.warnings) for a in artifacts),
            },
        )
        return 0
    finally:
        logger.flush()


def load_track(path: Path, logger: Logger | None = None) -> TrackArtifact:
    raw_text = path.read_text(encoding="utf-8")
    metadata_text, code = _split_front_matter(raw_text)
    metadata = None
    metadata_errors: List[str] = []
    metadata_warnings: List[str] = []

    if metadata_text is None:
        metadata_errors.append("YAML front matter block is required at top of file.")
    else:
        try:
            metadata = yaml.safe_load(metadata_text)
        except yaml.YAMLError as exc:
            metadata_errors.append(f"Failed to parse YAML front matter: {exc}")

    metadata_validation_errors: List[str] = []
    metadata_validation_warnings: List[str] = []
    if metadata_errors:
        metadata_validation_errors = metadata_errors
    else:
        metadata_validation_errors, metadata_validation_warnings = validate_metadata(metadata)

    code_errors: List[str]
    code_warnings: List[str]
    if metadata_validation_errors:
        # Still run code validation to surface more hints.
        code_errors, code_warnings = validate_pattern_code(code)
    else:
        code_errors, code_warnings = validate_pattern_code(code)

    errors = metadata_validation_errors + code_errors
    warnings = metadata_validation_warnings + code_warnings

    artifact = TrackArtifact(
        path=path,
        raw_content=raw_text,
        metadata=metadata,
        code=code,
        errors=errors,
        warnings=warnings,
        lint_error=None,
    )

    if logger:
        if errors:
            logger.error(
                "Validation failed",
                {"path": str(path), "errors": errors},
            )
        elif warnings:
            logger.warn(
                "Validation warnings",
                {"path": str(path), "warnings": warnings},
            )
        else:
            logger.info("Track OK", {"path": str(path)})

    return artifact


def _split_front_matter(raw_text: str) -> tuple[str | None, str | None]:
    if not raw_text.startswith("---"):
        return None, raw_text

    delimiter = "\n---"
    end_index = raw_text.find(delimiter, 3)
    if end_index == -1:
        delimiter = "\r\n---"
        end_index = raw_text.find(delimiter, 3)
        if end_index == -1:
            return None, raw_text

    metadata_text = raw_text[3:end_index]
    remainder_start = end_index + len(delimiter)
    remainder = raw_text[remainder_start:]
    if remainder.startswith("\r\n"):
        remainder = remainder[2:]
    elif remainder.startswith("\n"):
        remainder = remainder[1:]

    return metadata_text.strip(), remainder


def _write_outputs(
    artifacts: Sequence[TrackArtifact],
    out_dir: Path,
    formats: Set[str],
    logger: Logger,
) -> None:
    formats = {fmt.lower() for fmt in formats}
    unknown_formats = formats - SUPPORTED_FORMATS
    if unknown_formats:
        raise ValueError(f"Unsupported formats requested: {sorted(unknown_formats)}")

    out_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.utcnow().isoformat() + "Z"

    if "json" in formats:
        aggregate = {
            "generated_at": timestamp,
            "tracks": [
                {
                    "slug": artifact.slug,
                    "path": str(artifact.path),
                    "metadata": artifact.metadata,
                    "code": artifact.code,
                    "warnings": artifact.warnings,
                }
                for artifact in artifacts
            ],
        }
        (out_dir / "tracks.json").write_text(
            json.dumps(aggregate, indent=2),
            encoding="utf-8",
        )
        for artifact in artifacts:
            if artifact.slug:
                track_payload = {
                    "slug": artifact.slug,
                    "metadata": artifact.metadata,
                    "code": artifact.code,
                    "warnings": artifact.warnings,
                }
                (out_dir / f"{artifact.slug}.json").write_text(
                    json.dumps(track_payload, indent=2),
                    encoding="utf-8",
                )

    if "md" in formats:
        for artifact in artifacts:
            if not artifact.slug:
                continue
            metadata_display = json.dumps(artifact.metadata, indent=2)
            warnings_display = "\n".join(f"- {warning}" for warning in artifact.warnings)
            markdown = textwrap.dedent(
                f"""\
                # {artifact.metadata.get('title', artifact.slug)}

                **Slug:** `{artifact.slug}`  
                **Source:** `{artifact.path}`  
                **Warnings:**
                {warnings_display or "- none"}

                ## Metadata

                ```json
                {metadata_display}
                ```

                ## Pattern

                ```strudel
                {artifact.code or ''}
                ```
                """
            ).strip()
            (out_dir / f"{artifact.slug}.md").write_text(markdown + "\n", encoding="utf-8")

    if "raw" in formats:
        for artifact in artifacts:
            if not artifact.slug:
                continue
            (out_dir / f"{artifact.slug}.strudel").write_text(
                artifact.raw_content,
                encoding="utf-8",
            )

    logger.info(
        "Artifacts written",
        {"out_dir": str(out_dir), "formats": sorted(formats)},
    )


def _prepare_log_file(log_dir: Path) -> Path:
    log_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    return log_dir / f"compile-{timestamp}.log"


def _emit_report(logger: Logger, artifacts: Sequence[TrackArtifact], *, success: bool) -> None:
    report = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "success": success,
        "tracks": [
            {
                "slug": artifact.slug,
                "path": str(artifact.path),
                "errors": artifact.errors,
                "warnings": artifact.warnings,
            }
            for artifact in artifacts
        ],
    }
    logger.append_report(report)


__all__ = [
    "CompilationSettings",
    "TrackArtifact",
    "create_track_stub",
    "compile_project",
    "load_track",
]
