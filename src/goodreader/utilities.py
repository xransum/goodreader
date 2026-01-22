"""Utility helpers for caching, HTTP requests, and HTML parsing.

This module contains small, standalone functions used across the package:
- File-based JSON cache helpers stored under ``~/.cache/goodreads``.
- A minimal HTTP GET helper with basic URL validation.
- A helper to convert HTML into a BeautifulSoup object.
"""

from __future__ import annotations

import json
import os
import re
import time
import urllib.parse
from typing import Any, Dict, Optional

import requests
from bs4 import BeautifulSoup
from fake_headers import Headers

from goodreader.constants import ALLOWED_SCHEMES, DEFAULT_HEADERS


def get_cache_file_path(cache_file_name: str) -> str:
    """Return the absolute path to the JSON cache file.

    The cache directory is created if it does not already exist.

    Args:
        cache_file_name: Logical cache file name (without extension).

    Returns:
        Absolute filesystem path to ``{cache_file_name}.json`` under
        ``~/.cache/goodreads``.
    """
    cache_dir = os.path.expanduser("~/.cache/goodreads")
    os.makedirs(cache_dir, exist_ok=True)
    return os.path.join(cache_dir, f"{cache_file_name}.json")


def load_cache(cache_file_name: str) -> Dict[str, Any]:
    """Load cached JSON data.

    Args:
        cache_file_name: Logical cache file name (without extension).

    Returns:
        A dictionary of cached data. Returns an empty dict if the cache file
        does not exist.

    Raises:
        json.JSONDecodeError: If the cache file exists but contains invalid JSON.
        OSError: If reading the cache file fails.
    """
    cache_file_path = get_cache_file_path(cache_file_name)
    if os.path.exists(cache_file_path):
        with open(cache_file_path, "r") as f:
            return json.load(f)
    return {}


def save_cache(cache_file_name: str, data: Dict[str, Any]) -> None:
    """Write JSON-serializable data to the cache.

    Args:
        cache_file_name: Logical cache file name (without extension).
        data: Data to serialize and store in the cache.

    Raises:
        TypeError: If ``data`` is not JSON-serializable.
        OSError: If writing the cache file fails.
    """
    cache_file_path = get_cache_file_path(cache_file_name)
    with open(cache_file_path, "w") as f:
        json.dump(data, f)


def is_cache_valid(timestamp: float, ttl: int) -> bool:
    """Return whether a cached timestamp is still valid given a TTL.

    Args:
        timestamp: UNIX timestamp (seconds) indicating when the cache was written.
        ttl: Time-to-live in seconds. If ``ttl <= 0``, the cache is treated as
            always valid.

    Returns:
        True if the cache has not expired, otherwise False.
    """
    return (time.time() - timestamp) < ttl if ttl > 0 else True


def clear_cache(cache_file_name: str) -> None:
    """Delete the cache file if it exists.

    Args:
        cache_file_name: Logical cache file name (without extension).

    Raises:
        OSError: If removal fails for reasons other than non-existence.
    """
    cache_file_path = get_cache_file_path(cache_file_name)
    if os.path.exists(cache_file_path):
        os.remove(cache_file_path)


_WORD_SEP_RE = re.compile(r"[\s\-_]+")
_NON_ALNUM_RE = re.compile(r"[^a-z0-9\- ]+")


def slug_to_title(value: str) -> str:
    """Convert a slug (kebab/snake/mixed separators) into a title.

    Args:
        value: Input such as ``"hello-world"``, ``"hello_world"``, or
            ``"hello  world"``.

    Returns:
        Title-cased text with single spaces, e.g. ``"Hello World"``.
    """
    value = (value or "").strip()
    if not value:
        return ""

    parts = [p for p in _WORD_SEP_RE.split(value) if p]
    return " ".join(p.lower().capitalize() for p in parts)


def title_to_slug(value: str) -> str:
    """Convert a human-friendly title into a kebab-case slug.

    Args:
        value: Input such as ``"Hello World"`` (may contain punctuation).

    Returns:
        A lowercase kebab-case slug, e.g. ``"hello-world"``.
        Multiple separators collapse into one ``-`` and leading/trailing dashes
        are removed.
    """
    value = (value or "").strip().lower()
    if not value:
        return ""

    # Keep alnum, spaces, and dashes; drop other punctuation.
    value = _NON_ALNUM_RE.sub("", value)
    value = _WORD_SEP_RE.sub("-", value)
    return value.strip("-")


def get_request(
    url: str,
    params: Optional[Dict[str, str]] = None,
    *,
    timeout_seconds: float = 20.0,
) -> str:
    """Perform an HTTP GET request and return the response body as text.

    The URL scheme is validated against :data:`goodreader.constants.ALLOWED_SCHEMES`.

    Args:
        url: Base URL to request.
        params: Optional query parameters to be URL-encoded and appended.
        timeout_seconds: Request timeout in seconds.

    Returns:
        Response body decoded as text.

    Raises:
        ValueError: If ``url`` is empty or the URL scheme is not allowed.
        requests.RequestException: For network/HTTP errors.
    """
    if not url:
        raise ValueError("URL cannot be empty.")

    # Validate scheme using the base url (params are handled by requests)
    parsed = urllib.parse.urlparse(url)
    if parsed.scheme not in ALLOWED_SCHEMES:
        raise ValueError(
            f"Invalid URL scheme {parsed.scheme!r}. "
            f"Allowed schemes are: {', '.join(ALLOWED_SCHEMES)}"
        )

    header = Headers(headers=False)
    resp = requests.get(
        url,
        params=params,
        headers=header.generate(),  # dict(DEFAULT_HEADERS)
        timeout=timeout_seconds,
    )
    resp.raise_for_status()

    # Ensure correct decoding. requests uses charset from headers; fallback to apparent.
    if resp.encoding is None:
        resp.encoding = resp.apparent_encoding

    return resp.text


def soupify(html_content: str) -> BeautifulSoup:
    """Parse HTML into a BeautifulSoup object.

    Args:
        html_content: HTML document as a string.

    Returns:
        A BeautifulSoup instance using the built-in ``html.parser``.
    """
    return BeautifulSoup(html_content, "html.parser")
