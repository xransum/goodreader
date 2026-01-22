"""Genre command implementation.

This module contains the implementation behind the CLI subcommand:

    goodreader genre <keyword>
"""

from __future__ import annotations

import difflib

from goodreader.goodreads import GoodreadsClient
from goodreader.inputs import paginate
from goodreader.utilities import slug_to_title, title_to_slug


goodread = GoodreadsClient()

# Tuning knobs
_MAX_SUGGESTIONS = 10
# If best match score >= this and sufficiently ahead of the next one, auto-pick
_AUTO_PICK_CUTOFF = 0.90
_AUTO_PICK_MARGIN = 0.07


def _rank_genre_matches(
    keyword: str, genres: list[str]
) -> list[tuple[str, float]]:
    """Return genres ranked by similarity to keyword.

    Args:
        keyword: User-provided text (possibly already a slug).
        genres: List of available genre slugs.

    Returns:
        List of (genre_slug, score) sorted descending by score.
    """
    key = title_to_slug(keyword.strip())
    # Compare slugs-to-slugs for stable matching
    scored = [(g, difflib.SequenceMatcher(a=key, b=g).ratio()) for g in genres]
    scored.sort(key=lambda x: x[1], reverse=True)
    return scored


def genre_command(keyword: str, *, use_cache: bool = True) -> None:
    """Show details for a specific genre (with fuzzy matching)."""
    genres = goodread.get_genres()  # expected to be slugs
    if not genres:
        print("No genres available.")
        return

    key_slug = title_to_slug(keyword.strip())

    chosen: str | None = None
    auto_picked = False

    # Exact match (slug)
    if key_slug in genres:
        chosen = key_slug
    else:
        ranked = _rank_genre_matches(keyword, genres)
        best_slug, best_score = ranked[0]

        # Decide whether to auto-pick
        second_score = ranked[1][1] if len(ranked) > 1 else 0.0
        if (
            best_score >= _AUTO_PICK_CUTOFF
            and (best_score - second_score) >= _AUTO_PICK_MARGIN
        ):
            chosen = best_slug
            auto_picked = True
        else:
            # Otherwise offer a small list to choose from
            suggestions = ranked[:_MAX_SUGGESTIONS]
            titles = [
                f"{slug_to_title(slug)}  (match {score:.0%})"
                for slug, score in suggestions
            ]

            choice = paginate(
                titles,
                page_size=min(len(titles), _MAX_SUGGESTIONS),
                header=f"No exact genre match for '{keyword}'. Closest matches:",
                no_select=False,
            )
            if choice is None:
                return

            picked_index = titles.index(choice)
            chosen = suggestions[picked_index][0]

    assert chosen is not None

    titled_genre = slug_to_title(chosen)
    if auto_picked:
        print(f"Selected genre (auto): {titled_genre}")
    else:
        print(f"Selected genre: {titled_genre}")

    books = goodread.get_books_for_genre(chosen, use_cache=use_cache)
    print(f"Found {len(books)} books in genre '{titled_genre}'.")

    # Paginate and display books titles
    if books:
        print(books[0])


def execute(keyword: str, *, use_cache: bool = True) -> None:
    """CLI entry point for the standalone ``genre`` command module.

    Args:
        keyword: Genre name (or partial name) to search for.
        use_cache: If False, bypass cached genres list and cached books-for-genre results.
    """
    genre_command(keyword, use_cache=use_cache)
