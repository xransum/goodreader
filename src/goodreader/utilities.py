"""Module for package utility functions."""

import re
import urllib.parse
import urllib.request
from typing import Any, Dict, List, Optional

from bs4 import BeautifulSoup

from goodreader.constants import ALLOWED_SCHEMES, DEFAULT_HEADERS


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

