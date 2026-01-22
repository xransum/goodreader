"""Module for package utility functions."""

import json
import os
import re
import time
import urllib.parse
import urllib.request
from typing import Any, Dict, List, Optional

from bs4 import BeautifulSoup

from goodreader.constants import ALLOWED_SCHEMES, DEFAULT_HEADERS


def get_cache_file_path(cache_file_name: str) -> str:
    cache_dir = os.path.expanduser("~/.cache/goodreads")
    os.makedirs(cache_dir, exist_ok=True)
    return os.path.join(cache_dir, f"{cache_file_name}.json")


def load_cache(cache_file_name: str) -> Dict[str, Any]:
    cache_file_path = get_cache_file_path(cache_file_name)
    if os.path.exists(cache_file_path):
        with open(cache_file_path, "r") as f:
            return json.load(f)
    return {}


def save_cache(cache_file_name: str, data: Dict[str, Any]) -> None:
    cache_file_path = get_cache_file_path(cache_file_name)
    with open(cache_file_path, "w") as f:
        json.dump(data, f)


def is_cache_valid(timestamp: float, ttl: int) -> bool:
    return (time.time() - timestamp) < ttl if ttl > 0 else True


def clear_cache(cache_file_name: str) -> None:
    cache_file_path = get_cache_file_path(cache_file_name)
    if os.path.exists(cache_file_path):
        os.remove(cache_file_path)


def get_request(
    url: str,
    params: Optional[Dict[str, str]] = None,
) -> Any:
    """Get the content of a web page."""
    if not url:
        raise ValueError("URL cannot be empty.")

    # Construct the full URL with query parameters
    full_url = url
    if params is not None:
        full_url = f"{url}?{urllib.parse.urlencode(params)}"

    # Parse the URL to validate the scheme
    parsed = urllib.parse.urlparse(full_url)
    if parsed.scheme not in ALLOWED_SCHEMES:
        raise ValueError(
            f"Invalid URL scheme {parsed.scheme!r}. "
            f"Allowed schemes are: {', '.join(ALLOWED_SCHEMES)}"
        )

    # Create the request
    headers = DEFAULT_HEADERS
    req = urllib.request.Request(full_url, headers=headers)
    # with urllib.request.urlopen(req) as res:
    #     return res.read()
    return urllib.request.urlopen(req).read()


def soupify(html_content: str) -> BeautifulSoup:
    """Convert HTML content to a BeautifulSoup object."""
    return BeautifulSoup(html_content, "html.parser")
