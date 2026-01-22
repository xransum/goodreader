"""Cache module for persistent data."""

import json
import os
import time
from pathlib import Path
from typing import Any, Optional


class Cache:
    """File-based cache with TTL under ~/.cache/goodreads/<name>."""

    def __init__(self, name: str, ttl_seconds: int = 3600) -> None:
        # Optimized constants and resolved paths once
        self._home = Path.home()
        self._base_cache_dir = self._home / ".cache" / "goodreads"
        self._base_cache_dir.mkdir(parents=True, exist_ok=True)

        # Single responsibility constants
        self._name = f"{name}.json"
        self._path = self._base_cache_dir / self._name
        self._ttl = ttl_seconds

    def is_expired(self) -> bool:
        if not self._path.exists():
            return True
        mtime = self._path.stat().st_mtime
        return (time.time() - mtime) > self._ttl

    def get(self) -> Optional[Any]:
        if self.is_expired():
            return None
        try:
            with self._path.open("r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError):
            return None

    def set(self, data: Any) -> None:
        try:
            with self._path.open("w", encoding="utf-8") as f:
                json.dump(data, f)
        except OSError:
            # Best-effort cache; ignore write failures
            pass

    @property
    def path(self) -> Path:
        return self._path

    @property
    def ttl(self) -> int:
        return self._ttl
