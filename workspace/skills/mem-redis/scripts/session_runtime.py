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
import stat as stat_module
from pathlib import Path
from typing import Iterable, List, Optional, Sequence, Tuple


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


def _is_listable_dir(path: Path) -> bool:
    try:
        if not path.is_dir():
            return False
        iterator = path.iterdir()
        next(iterator, None)
        return True
    except OSError:
        return False


def discover_session_dirs(explicit_dir: Optional[str] = None) -> List[Path]:
    if explicit_dir:
        path = Path(explicit_dir).expanduser()
        return [path] if _is_listable_dir(path) else []

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
    return [path for path in _unique_paths(paths) if _is_listable_dir(path)]


def _readable_transcript_entries(session_dir: Path) -> List[Tuple[float, Path]]:
    entries: List[Tuple[float, Path]] = []
    try:
        candidates = list(session_dir.glob("*.jsonl"))
    except OSError:
        return entries

    for transcript in candidates:
        try:
            stat_result = transcript.stat()
        except OSError:
            continue
        if not stat_module.S_ISREG(stat_result.st_mode):
            continue
        entries.append((stat_result.st_mtime, transcript))
    return entries


def find_latest_transcript(session_dirs: Sequence[Path]) -> Optional[Path]:
    for session_dir in session_dirs:
        readable = _readable_transcript_entries(session_dir)
        if not readable:
            continue
        return max(readable, key=lambda item: item[0])[1]
    return None


def find_all_transcripts(session_dirs: Sequence[Path]) -> List[Path]:
    transcripts: List[Path] = []
    for session_dir in session_dirs:
        readable = sorted(_readable_transcript_entries(session_dir), key=lambda item: item[0])
        transcripts.extend(path for _, path in readable)
    return transcripts
