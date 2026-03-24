#!/usr/bin/env python3
"""
Helpers for choosing the active OpenClaw session directory.

CodeShield deployments often run the live OpenClaw process under the isolated
`openclaw-svc` runtime while legacy home-session files still exist under the
interactive `openclaw` account. Cron and heartbeat jobs should follow the
runtime with the newest transcript activity instead of assuming one fixed path.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Iterable, List, Optional, Sequence


def _unique_paths(paths: Iterable[Path]) -> List[Path]:
    unique: List[Path] = []
    seen = set()
    for path in paths:
        resolved = str(path)
        if resolved in seen:
            continue
        seen.add(resolved)
        unique.append(path)
    return unique


def _is_readable_dir(path: Path) -> bool:
    try:
        return path.is_dir()
    except OSError:
        return False


def discover_session_dirs(explicit_dir: Optional[str] = None) -> List[Path]:
    if explicit_dir:
        path = Path(explicit_dir).expanduser()
        return [path] if _is_readable_dir(path) else []

    default_home_sessions = Path.home() / ".openclaw" / "agents" / "main" / "sessions"
    default_service_sessions = Path("/var/lib/openclaw-svc/.openclaw/agents/main/sessions")

    candidates = [
        os.getenv("OPENCLAW_SERVICE_SESSIONS_DIR", ""),
        os.getenv("OPENCLAW_SESSIONS_DIR", ""),
        os.getenv("OPENCLAW_HOME_SESSIONS_DIR", ""),
        str(default_service_sessions),
        str(default_home_sessions),
    ]

    paths = [Path(value).expanduser() for value in candidates if value]
    return [path for path in _unique_paths(paths) if _is_readable_dir(path)]


def find_latest_transcript(session_dirs: Sequence[Path]) -> Optional[Path]:
    for session_dir in session_dirs:
        transcripts: List[Path] = []
        try:
            transcripts.extend(path for path in session_dir.glob("*.jsonl") if path.is_file())
        except OSError:
            continue
        if not transcripts:
            continue
        readable = []
        for transcript in transcripts:
            try:
                transcript.stat()
            except OSError:
                continue
            readable.append(transcript)
        if readable:
            return max(readable, key=lambda path: path.stat().st_mtime)
    return None


def find_all_transcripts(session_dirs: Sequence[Path]) -> List[Path]:
    transcripts: List[Path] = []
    for session_dir in session_dirs:
        try:
            candidates = [path for path in session_dir.glob("*.jsonl") if path.is_file()]
        except OSError:
            continue
        readable: List[Path] = []
        for transcript in candidates:
            try:
                transcript.stat()
            except OSError:
                continue
            readable.append(transcript)
        transcripts.extend(sorted(readable, key=lambda path: path.stat().st_mtime))
    return transcripts
