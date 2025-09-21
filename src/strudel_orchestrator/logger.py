"""Lightweight structured logger with optional file output."""

from __future__ import annotations

import json
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

_LOG_LEVELS: Dict[str, int] = {
    "silent": 0,
    "error": 1,
    "warn": 2,
    "info": 3,
    "debug": 4,
}


@dataclass(slots=True)
class LoggerConfig:
    level: str = "info"
    log_file: Optional[Path] = None


class Logger:
    """Console + file logger aware of log levels."""

    def __init__(self, config: LoggerConfig | None = None) -> None:
        cfg = config or LoggerConfig()
        self.level = self._normalize_level(cfg.level)
        self._threshold = _LOG_LEVELS[self.level]
        self._log_path = cfg.log_file
        self._stream = (
            cfg.log_file.open("a", encoding="utf-8") if cfg.log_file else None
        )

    def debug(self, message: str, meta: Optional[Dict[str, Any]] = None) -> None:
        self._log("debug", message, meta)

    def info(self, message: str, meta: Optional[Dict[str, Any]] = None) -> None:
        self._log("info", message, meta)

    def warn(self, message: str, meta: Optional[Dict[str, Any]] = None) -> None:
        self._log("warn", message, meta)

    def error(self, message: str, meta: Optional[Dict[str, Any]] = None) -> None:
        self._log("error", message, meta)

    def append_report(self, report: Dict[str, Any]) -> None:
        if not self._stream:
            return
        self._stream.write(json.dumps({"report": report}, indent=2) + "\n")

    def flush(self) -> None:
        if self._stream:
            self._stream.flush()
            self._stream.close()
            self._stream = None

    def _log(
        self, level: str, message: str, meta: Optional[Dict[str, Any]] = None
    ) -> None:
        timestamp = datetime.utcnow().isoformat() + "Z"
        header = f"[{timestamp}] [{level.upper()}] {message}"
        numeric_level = _LOG_LEVELS[level]

        if numeric_level <= self._threshold and self._threshold > 0:
            if meta:
                console_meta = self._format_meta(meta)
                print(header, console_meta, file=sys.stdout)
            else:
                print(header, file=sys.stdout)
        elif level == "error" and self._threshold == 0:
            console_meta = self._format_meta(meta)
            print(header, console_meta, file=sys.stderr)

        if self._stream:
            self._stream.write(header + "\n")
            if meta:
                self._stream.write(json.dumps({"meta": meta}, indent=2) + "\n")

    @staticmethod
    def _normalize_level(level: Optional[str]) -> str:
        if not level:
            return "info"
        normalized = level.lower()
        return normalized if normalized in _LOG_LEVELS else "info"

    @staticmethod
    def _format_meta(meta: Dict[str, Any]) -> str:
        try:
            return json.dumps(meta, separators=(",", ":"))
        except (TypeError, ValueError):
            return "{\"meta\": " + repr(meta) + "}"


__all__ = ["Logger", "LoggerConfig", "_LOG_LEVELS"]
