"""Genres command implementation.

This module implements the CLI subcommand:

    goodreader genres

At the moment this is a placeholder that prints a static list of genres; replace
:func:`list_genres` with real lookup logic (API call, scraper, database query,
etc.).
"""

from goodreader.goodreads import GoodreadsClient
from goodreader.inputs import paginate
from goodreader.utilities import slug_to_title, title_to_slug


goodread = GoodreadsClient()
page_size = 20


def list_genres(*, use_cache: bool = True) -> None:
    """List available genres and print them to stdout.

    Args:
        use_cache: If False, bypass any cached genre list and fetch fresh data.
    """
    genres = goodread.get_genres(use_cache=use_cache)
    titled_genres = [slug_to_title(g) for g in genres]

    choice = paginate(
        titled_genres,
        page_size=page_size,
        header="Available Genres:",
        no_select=True,
    )
    if choice is None:
        return

    print(f"You selected: {choice}")
    # We need to setup some level of pagination here
    # as there are thousands of genres


def execute(*, use_cache: bool = True) -> None:
    """CLI entry point for the standalone ``genres`` command module."""
    list_genres(use_cache=use_cache)
