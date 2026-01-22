"""Interactive input helpers for CLI workflows.

This module contains small utilities used by CLI commands that need to prompt
the user (e.g., pagination).
"""

from __future__ import annotations

from collections.abc import Callable, Sequence
from typing import TypeVar


T = TypeVar("T")


def paginate(
    items: Sequence[T],
    *,
    page_size: int = 20,
    render_item: Callable[[T], str] | None = None,
    header: str | None = None,
    prompt: str | None = None,
    no_select: bool = False,
) -> T | None:
    """Paginate results interactively and optionally return a selected item.

    The UI is designed for two tasks:
      1) Navigate pages of results.
      2) Optionally select an item from the currently displayed page.

    Controls:
        - On start, page 1 is displayed automatically.
        - Enter ``n`` for next page, ``p`` for previous page.
        - Enter ``g`` to go to a specific page (then enter the page number).
        - Enter ``b`` to go back to the previous page.
        - Enter ``q`` at any prompt to quit (returns None).
        - If ``no_select`` is False:
            * Enter an item number (global index shown in the list) to select an item.

    Args:
        items: Full result set to paginate.
        page_size: Number of items per page. Must be > 0.
        render_item: Optional per-item formatter. Defaults to ``str``.
        header: Optional header printed above each page.
        prompt: Optional page prompt override. If omitted, a default prompt like
            ``"Input page number 1..N (q to quit): "`` is used.
        no_select: If True, disables item selection and only allows navigation.
            The function will always return None in this mode.

    Returns:
        The selected item (if selection is enabled), or None if the user quits /
        interrupts / no results / or ``no_select`` is True.

    Raises:
        ValueError: If ``page_size <= 0``.
    """
    if page_size <= 0:
        raise ValueError("page_size must be > 0")

    total = len(items)
    if total == 0:
        print("No results.")
        return None

    render = render_item or (lambda x: str(x))
    pages = (total + page_size - 1) // page_size

    page_prompt = prompt or f"Input page number 1..{pages} (q to quit): "

    def _render_page(page: int) -> tuple[int, int]:
        """Render page and return (start_index, end_index_exclusive)."""
        start = (page - 1) * page_size
        end = min(start + page_size, total)

        if header:
            print(header)

        print(f"Page {page}/{pages} ({start + 1}-{end} of {total})")
        for global_idx, item in enumerate(items[start:end], start=start + 1):
            print(f"{global_idx}. {render(item)}")
        print()
        return start, end

    page = 1

    while True:
        start, end = _render_page(page)

        low = start + 1
        high = end

        if no_select:
            nav_prompt = "n=next p=prev g=goto b=back q=quit: "
        else:
            nav_prompt = (
                f"Select {low}..{high} | n=next p=prev g=goto b=back q=quit: "
            )

        try:
            cmd = input(nav_prompt).strip().lower()
        except (EOFError, KeyboardInterrupt):
            print()
            return None

        if cmd == "":
            continue
        if cmd == "q":
            return None

        if cmd == "n":
            if page < pages:
                page += 1
            else:
                print("Already at last page.")
            continue

        if cmd == "p" or cmd == "b":
            # Back means previous page.
            if page > 1:
                page -= 1
            else:
                print("Already at first page.")
            continue

        if cmd == "g":
            try:
                goto_raw = input(page_prompt).strip().lower()
            except (EOFError, KeyboardInterrupt):
                print()
                return None

            if goto_raw == "":
                continue
            if goto_raw == "q":
                return None

            try:
                goto_page = int(goto_raw)
            except ValueError:
                print(
                    f"Invalid input: {goto_raw!r}. Enter a number 1..{pages} (q to quit)."
                )
                continue

            if not (1 <= goto_page <= pages):
                print(f"Out of range. Enter a number 1..{pages} (q to quit).")
                continue

            page = goto_page
            continue

        if no_select:
            print("Invalid input. Use n/p/g/b/q.")
            continue

        # Otherwise, treat as item selection by *global* index.
        try:
            pick = int(cmd)
        except ValueError:
            print("Invalid input. Enter an item number or n/p/g/b/q.")
            continue

        if not (low <= pick <= high):
            print(f"Out of range. Enter {low}..{high}.")
            continue

        return items[pick - 1]
