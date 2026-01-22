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


def list_genres() -> None:
    """List available genres and print them to stdout.

    Notes:
        This is currently a placeholder implementation that uses a hard-coded
        list. A real implementation would likely fetch genres from a remote
        service or a local dataset.
    """
    genres = goodread.get_genres()
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


def execute() -> None:
    """CLI entry point for the standalone ``genres`` command module."""
    list_genres()
