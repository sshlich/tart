from pathlib import Path

from strudel_orchestrator.orchestrator import CompilationSettings, compile_project


def test_compile_check_only_succeeds(tmp_path: Path):
    # Use current project tracks directory
    project_root = Path(__file__).resolve().parents[1]
    tracks_dir = project_root / "tracks"

    out_dir = tmp_path / "dist"
    settings = CompilationSettings(
        tracks_dir=tracks_dir,
        out_dir=out_dir,
        formats={"json"},
        check_only=True,
        log_dir=tmp_path / "logs",
        log_level="info",
    )
    # Should return 0 on success
    assert compile_project(settings) == 0


def test_compile_flags_malformed_front_matter(tmp_path: Path):
    # Create a bad track missing YAML delimiter
    bad_track = tmp_path / "tracks" / "bad.strudel"
    bad_track.parent.mkdir(parents=True, exist_ok=True)
    bad_track.write_text("setcpm(120)\ns(\"bd\")\n", encoding="utf-8")

    out_dir = tmp_path / "dist"
    settings = CompilationSettings(
        tracks_dir=bad_track.parent,
        out_dir=out_dir,
        formats={"json"},
        check_only=True,
        log_dir=tmp_path / "logs",
        log_level="info",
    )
    # Should return non-zero due to validation error
    assert compile_project(settings) == 1
