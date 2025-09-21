"""Audio splicing utilities built on ffmpeg."""
from __future__ import annotations

import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Sequence

from .logger import Logger


@dataclass(slots=True)
class SplicePlan:
    inputs: Sequence[Path]
    output: Path


def _run_ffmpeg(args: list[str]) -> None:
    subprocess.run(["ffmpeg", "-y", *args], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)


def concat_audio(inputs: Sequence[Path], output: Path, logger: Logger | None = None) -> Path:
    if not inputs:
        raise ValueError("No input files supplied for concat")
    output.parent.mkdir(parents=True, exist_ok=True)

    # Use concat demuxer
    # Create a temporary list file
    list_path = output.with_suffix(output.suffix + ".list")
    list_path.write_text("\n".join(f"file '{p}'" for p in inputs), encoding="utf-8")
    try:
        _run_ffmpeg(["-f", "concat", "-safe", "0", "-i", str(list_path), str(output)])
    finally:
        try:
            list_path.unlink(missing_ok=True)
        except Exception:
            pass
    if logger:
        logger.info("Concatenated audio", {"inputs": [str(p) for p in inputs], "output": str(output)})
    return output


def loop_audio(input_path: Path, repeats: int, output: Path, logger: Logger | None = None) -> Path:
    if repeats < 1:
        raise ValueError("repeats must be >= 1")
    output.parent.mkdir(parents=True, exist_ok=True)
    # Build a concat via filter_complex with multiple copies
    filter_inputs = []
    args = ["-i", str(input_path)] * repeats
    for i in range(repeats):
        filter_inputs.append(f"[{i}:a]")
    filtergraph = "".join(filter_inputs) + f"concat=n={repeats}:v=0:a=1[out]"
    _run_ffmpeg([*args, "-filter_complex", filtergraph, "-map", "[out]", str(output)])
    if logger:
        logger.info("Looped audio", {"input": str(input_path), "repeats": repeats, "output": str(output)})
    return output
