"""Command-line interface for the Strudel orchestrator."""

from __future__ import annotations

import argparse
from datetime import datetime
from pathlib import Path
from typing import Sequence
import subprocess
import shutil

from .logger import Logger, LoggerConfig, _LOG_LEVELS
from .orchestrator import (
    CompilationSettings,
    compile_project,
    create_track_stub,
)
from .renderer import RenderOptions, render_tracks
from .splicer import concat_audio, loop_audio


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="strudel-orchestrator",
        description="Compile Strudel tracks with metadata validation and artifact export.",
    )
    subparsers = parser.add_subparsers(dest="command")

    init_parser = subparsers.add_parser(
        "init",
        help="Create a new .strudel track scaffold.",
    )
    init_parser.add_argument("slug", help="Track identifier (kebab-case).")
    init_parser.add_argument(
        "--title",
        help="Optional human-readable title. Defaults to title-cased slug.",
    )
    init_parser.add_argument(
        "--tempo",
        type=int,
        default=90,
        help="Initial cycles per minute for the template (default: 90).",
    )
    init_parser.add_argument(
        "--tracks-dir",
        default="tracks",
        help="Directory to place the new .strudel file (default: tracks).",
    )
    init_parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite existing file if present.",
    )

    compile_parser = subparsers.add_parser(
        "compile",
        help="Validate tracks and emit compilation artifacts.",
    )
    compile_parser.add_argument(
        "--tracks-dir",
        default="tracks",
        help="Directory containing .strudel sources (default: tracks).",
    )
    compile_parser.add_argument(
        "--out",
        default="dist",
        help="Output directory for generated artifacts (default: dist).",
    )
    compile_parser.add_argument(
        "--format",
        default="json,md,raw",
        help="Comma-separated list of artifact formats to emit (json, md, raw).",
    )
    compile_parser.add_argument(
        "--check-only",
        action="store_true",
        help="Run validations without writing output files.",
    )
    compile_parser.add_argument(
        "--log-level",
        default="info",
        choices=sorted(_LOG_LEVELS.keys()),
        help="Logging verbosity (default: info).",
    )
    compile_parser.add_argument(
        "--log-dir",
        default="logs",
        help="Directory for structured log files (default: logs).",
    )

    render_parser = subparsers.add_parser(
        "render",
        help="Bounce Strudel patterns to audio files (requires Playwright and ffmpeg).",
    )
    render_parser.add_argument(
        "--tracks-dir",
        default="tracks",
        help="Directory containing .strudel sources (default: tracks).",
    )
    render_parser.add_argument(
        "--out",
        default="audio",
        help="Directory for rendered audio (default: audio).",
    )
    render_parser.add_argument(
        "--format",
        default="wav",
        help="Comma-separated audio formats to emit (supports wav).",
    )
    render_parser.add_argument(
        "--duration",
        type=float,
        default=8.0,
        help="Capture duration in seconds after warmup (default: 8).",
    )
    render_parser.add_argument(
        "--warmup",
        type=float,
        default=4.0,
        help="Warmup time in seconds before recording (default: 4).",
    )
    render_parser.add_argument(
        "--log-level",
        default="info",
        choices=sorted(_LOG_LEVELS.keys()),
        help="Logging verbosity (default: info).",
    )
    render_parser.add_argument(
        "--log-dir",
        default="logs",
        help="Directory for render logs (default: logs).",
    )
    render_parser.add_argument(
        "--slug",
        action="append",
        default=[],
        help="Render only specific track slugs (can be passed multiple times).",
    )
    render_parser.add_argument(
        "--play-expr",
        default=None,
        help="Append a Strudel expression after the track code (e.g., arrangement macro).",
    )

    fetch_parser = subparsers.add_parser(
        "fetch-strudel",
        help="Shallow, sparse-clone the Strudel repo into vendor/ for local inspection.",
    )
    suite_parser = subparsers.add_parser(
        "render-suite",
        help="Render multiple variants for one or more tracks and rotate audio directories.",
    )
    suite_parser.add_argument("--tracks-dir", default="tracks")
    suite_parser.add_argument("--out", default="audio")
    suite_parser.add_argument("--slug", action="append", default=[])
    suite_parser.add_argument("--warmup", type=float, default=4.0)
    suite_parser.add_argument("--duration", type=float, default=8.0)
    suite_parser.add_argument("--formats", default="wav")
    suite_parser.add_argument(
        "--variants",
        action="append",
        default=[""],
        help="Strudel expressions to append for each variant (repeatable). Empty string means base track.",
    )
    suite_parser.add_argument(
        "--rotate",
        action="store_true",
        help="Move existing audio/ to audio_OLD/ before writing new renders.",
    )

    splice_parser = subparsers.add_parser(
        "splice",
        help="Concatenate multiple audio files into one output using ffmpeg.",
    )
    splice_parser.add_argument(
        "--inputs",
        action="append",
        required=True,
        help="Input audio files in order (repeat this flag for each input).",
    )
    splice_parser.add_argument(
        "--out",
        required=True,
        help="Output audio file path (extension determines format).",
    )

    loop_parser = subparsers.add_parser(
        "loop",
        help="Loop a single audio file N times using ffmpeg and write output.",
    )
    loop_parser.add_argument("--input", required=True, help="Input audio file to loop.")
    loop_parser.add_argument("--repeats", type=int, required=True, help="Number of repeats (>=1).")
    loop_parser.add_argument("--out", required=True, help="Output audio file path.")
    fetch_parser.add_argument(
        "--repo-url",
        default="https://codeberg.org/uzu/strudel.git",
        help="Git URL of the Strudel repository (default: codeberg).",
    )
    fetch_parser.add_argument(
        "--dest",
        default="vendor/strudel",
        help="Destination directory for the clone (default: vendor/strudel).",
    )
    fetch_parser.add_argument(
        "--sparse",
        action="append",
        default=["packages/web", "packages/repl", "docs", "examples"],
        help="Sparse-checkout directories to include (repeatable). Defaults include web, repl, docs, examples.",
    )
    fetch_parser.add_argument(
        "--include",
        action="append",
        default=["README.md"],
        help="Additional top-level files to include (repeatable). Default: README.md",
    )
    fetch_parser.add_argument(
        "--force",
        action="store_true",
        help="Remove existing destination before cloning.",
    )

    args = parser.parse_args(argv)

    if args.command == "init":
        return _handle_init(args)
    if args.command == "compile":
        return _handle_compile(args)
    if args.command == "render":
        return _handle_render(args)
    if args.command == "fetch-strudel":
        return _handle_fetch_strudel(args)
    if args.command == "render-suite":
        return _handle_render_suite(args)
    if args.command == "splice":
        return _handle_splice(args)
    if args.command == "loop":
        return _handle_loop(args)

    parser.print_help()
    return 0


def _handle_init(args: argparse.Namespace) -> int:
    tracks_dir = Path(args.tracks_dir)
    try:
        target = create_track_stub(
            args.slug,
            title=args.title,
            tempo=args.tempo,
            tracks_dir=tracks_dir,
            force=args.force,
        )
    except (ValueError, FileExistsError) as exc:
        print(f"Error: {exc}")
        return 1

    print(f"Created track scaffold at {target}")
    return 0


def _handle_compile(args: argparse.Namespace) -> int:
    formats = {
        part.strip().lower()
        for part in args.format.split(",")
        if part.strip()
    }
    if not formats:
        formats = {"json", "md", "raw"}

    settings = CompilationSettings(
        tracks_dir=Path(args.tracks_dir),
        out_dir=Path(args.out),
        formats=formats,
        check_only=args.check_only,
        log_dir=Path(args.log_dir),
        log_level=args.log_level,
    )

    return compile_project(settings)


def _handle_render(args: argparse.Namespace) -> int:
    formats = {
        part.strip().lower()
        for part in args.format.split(",")
        if part.strip()
    }
    if not formats:
        formats = {"wav", "mp3"}

    log_dir = Path(args.log_dir)
    log_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    log_file = log_dir / f"render-{timestamp}.log"
    logger = Logger(LoggerConfig(level=args.log_level, log_file=log_file))

    options = RenderOptions(
        tracks_dir=Path(args.tracks_dir),
        out_dir=Path(args.out),
        formats=tuple(formats),
        duration_ms=int(args.duration * 1000),
        warmup_ms=int(args.warmup * 1000),
        slugs=tuple(args.slug),
        play_expr=args.play_expr,
    )

    try:
        render_tracks(options, logger)
    finally:
        logger.flush()

    return 0


def _run(cmd: list[str], cwd: Path | None = None) -> None:
    subprocess.run(cmd, check=True, cwd=str(cwd) if cwd else None, stdout=subprocess.PIPE, stderr=subprocess.PIPE)


def _handle_fetch_strudel(args: argparse.Namespace) -> int:
    repo_url = args.repo_url
    dest = Path(args.dest)
    if dest.exists() and args.force:
        shutil.rmtree(dest)
    dest.parent.mkdir(parents=True, exist_ok=True)

    try:
        _run(["git", "clone", "--depth", "1", "--filter=blob:none", "--sparse", repo_url, str(dest)])
        # enable cone mode then set sparse dirs
        _run(["git", "sparse-checkout", "set", "--cone"], cwd=dest)
        if args.sparse:
            _run(["git", "sparse-checkout", "set", *args.sparse], cwd=dest)
        # include extra files (like README.md)
        for include_path in args.include or []:
            _run(["git", "sparse-checkout", "add", "--skip-checks", include_path], cwd=dest)
    except subprocess.CalledProcessError as exc:
        # surface stderr for easier debugging
        try:
            stderr = exc.stderr.decode()
        except Exception:
            stderr = str(exc)
        print(f"Error: git operation failed. {stderr}")
        return 1

    print(f"Strudel repository fetched into {dest}")
    return 0


def _handle_render_suite(args: argparse.Namespace) -> int:
    out_dir = Path(args.out)
    if args.rotate and out_dir.exists():
        old_dir = out_dir.with_name(out_dir.name + "_OLD")
        if old_dir.exists():
            import shutil
            shutil.rmtree(old_dir)
        out_dir.rename(old_dir)

    formats = {
        part.strip().lower()
        for part in str(args.formats).split(",")
        if part.strip()
    }
    if not formats:
        formats = {"wav", "mp3"}

    # For each variant, render into a subfolder like audio/<slug>/<variant_idx>/
    total = 0
    for slug in (args.slug or []):
        for idx, play_expr in enumerate(args.variants or [""]):
            variant_out = out_dir / slug / f"v{idx:02d}"
            options = RenderOptions(
                tracks_dir=Path(args.tracks_dir),
                out_dir=variant_out,
                formats=tuple(formats),
                duration_ms=int(args.duration * 1000),
                warmup_ms=int(args.warmup * 1000),
                slugs=(slug,),
                play_expr=play_expr or None,
            )
            total += render_tracks(options, Logger(LoggerConfig(level="info", log_file=None)))

    print(f"Rendered {total} track variants into {out_dir}")
    return 0


def _handle_splice(args: argparse.Namespace) -> int:
    logger = Logger(LoggerConfig(level="info", log_file=None))
    inputs = [Path(p) for p in (args.inputs or [])]
    output = Path(args.out)
    if not inputs:
        print("Error: at least one --inputs is required")
        return 1
    try:
        concat_audio(inputs, output, logger)
    except subprocess.CalledProcessError as exc:
        print("Error: ffmpeg failed during concat")
        return 1
    print(f"Spliced {len(inputs)} files into {output}")
    return 0


def _handle_loop(args: argparse.Namespace) -> int:
    logger = Logger(LoggerConfig(level="info", log_file=None))
    input_path = Path(args.input)
    output = Path(args.out)
    repeats = int(args.repeats)
    try:
        loop_audio(input_path, repeats, output, logger)
    except subprocess.CalledProcessError as exc:
        print("Error: ffmpeg failed during loop")
        return 1
    print(f"Looped {input_path} x{repeats} into {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
