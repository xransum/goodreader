"""Wrapper API for Goodreads."""

import logging
import re
from pathlib import Path

from goodreader.cache import Cache
from goodreader.utilities import get_request, soupify


# Set up logger for this module
logger = logging.getLogger(__name__)

RATING_RE = re.compile(r"avg rating\s+([0-9.]+)", re.IGNORECASE)
RATINGS_COUNT_RE = re.compile(r"([0-9][0-9,]*)\s+ratings", re.IGNORECASE)
PUBLISHED_YEAR_RE = re.compile(r"published\s+(\d{4})", re.IGNORECASE)


class GoodreadsClient:
    """Goodreads API wrapper."""

    BASE_URL = "https://www.goodreads.com"
    DEFAULT_CACHE_TTL = 86400  # 24 hours
    CACHE_KEY_GENRES = "genres"
    CACHE_KEY_BOOKS_FOR_GENRE = "books_for_genre"

    def _normalize_genre_slug(self, genre: str) -> str:
        """Normalize genre slug for cache key."""
        # Goodreads shelf slugs are typically hyphenated; normalize defensively.
        return genre.strip().lower().replace(" ", "-")

    def _books_for_genre_cache_key(self, genre: str) -> str:
        """Generate cache key for books of a specific genre."""
        return f"{self.CACHE_KEY_BOOKS_FOR_GENRE}:{self._normalize_genre_slug(genre)}"

    def get_genres(self, use_cache: bool = True) -> list:
        """Get list of genres from Goodreads."""
        logger.info("Fetching genres (use_cache=%s)", use_cache)
        cache = Cache(self.CACHE_KEY_GENRES, ttl_seconds=self.DEFAULT_CACHE_TTL)
        if use_cache:
            cached_data = cache.get()
            if cached_data is not None:
                logger.debug("Cache hit for genres (%d items)", len(cached_data))
                return cached_data

            logger.debug("Cache miss for genres")

        genres = []
        page = 1

        while True:
            logger.debug("Fetching genres page %d", page)
            content = self._get_genres_pagination(page)
            soup = soupify(content)

            page_genres = self._extract_genres_from_soup(soup)
            if page_genres:
                genres.extend(page_genres)

            if not self._has_next_page(soup):
                break

            page += 1

        logger.info("Fetched total of %d genres", len(genres))
        cache.set(genres)
        return genres

    def _has_next_page(self, soup) -> bool:
        """Return True if the parsed page has a usable 'next page' link."""
        return self._get_next_page_href(soup) is not None

    def get_books_for_genre(
        self,
        genre: str,
        *,
        use_cache: bool = True,
        max_pages: int | None = 200,
        dump_pages_dir: str | Path | None = ".",
    ) -> list:
        """Get list of books for a given genre from Goodreads.

        Args:
            genre: Goodreads shelf slug (e.g. "science-fiction").
            use_cache: If False, bypass any cached results and fetch fresh data.
            max_pages: Safety cap to avoid infinite loops. Set None to disable.
            dump_pages_dir: If set, write each fetched HTML page to this directory.
                For debugging only. Defaults to current directory.
        """
        cache_key = self._books_for_genre_cache_key(genre)
        cache = Cache(cache_key, ttl_seconds=self.DEFAULT_CACHE_TTL)

        logger.info(
            "Fetching books for genre: %s (use_cache=%s)", genre, use_cache
        )

        # If we're dumping pages, avoid serving stale cached HTML-derived results.
        if use_cache and dump_pages_dir is None:
            cached_data = cache.get()
            if cached_data is not None:
                logger.debug(
                    "Cache hit for books genre '%s' (%d items)",
                    genre,
                    len(cached_data),
                )
                return cached_data
            logger.debug("Cache miss for books genre '%s'", genre)

        dump_dir: Path | None = None
        if dump_pages_dir is not None:
            dump_dir = Path(dump_pages_dir).expanduser().resolve()
            dump_dir.mkdir(parents=True, exist_ok=True)

        books: list[dict] = []
        seen_keys: set[tuple[str, str, int]] = set()
        seen_page_signatures: set[tuple[tuple[str, str, int], ...]] = set()

        page = 1
        while True:
            if max_pages is not None and page > max_pages:
                logger.warning(
                    "Stopping pagination for genre '%s' after max_pages=%d",
                    genre,
                    max_pages,
                )
                break

            logger.debug("Fetching books for genre '%s', page %d", genre, page)
            content = self._get_books_for_genre_pagination(genre, page)
            soup = soupify(content)

            page_books = self._extract_books_from_soup(soup)
            if not page_books:
                logger.debug(
                    "No books extracted for genre '%s' page %d; stopping",
                    genre,
                    page,
                )
                break

            # Build stable keys for dedupe/loop detection
            page_keys: list[tuple[str, str, int]] = []
            for b in page_books:
                title = (b.get("title") or "").strip().lower()
                author = (b.get("author") or "").strip().lower()
                year = b.get("published_year") or 0
                page_keys.append((title, author, int(year)))

            # Signature-based loop detection (exact same page repeated)
            signature = tuple(page_keys)
            if signature in seen_page_signatures:
                logger.warning(
                    "Detected repeated page signature for genre '%s' page %d; stopping",
                    genre,
                    page,
                )
                break
            seen_page_signatures.add(signature)

            # Only add truly new books
            added = 0
            for b, k in zip(page_books, page_keys):
                if k in seen_keys:
                    continue
                seen_keys.add(k)
                books.append(b)
                added += 1

            logger.debug(
                "Genre '%s' page %d: extracted=%d added_new=%d total=%d",
                genre,
                page,
                len(page_books),
                added,
                len(books),
            )

            # If we didn't add anything new, we are looping / stuck
            if added == 0:
                logger.warning(
                    "No new books added for genre '%s' on page %d (likely dup/loop); stopping",
                    genre,
                    page,
                )
                break

            page += 1

        logger.info(
            "Fetched total of %d books for genre '%s'", len(books), genre
        )

        # Don’t cache an instrumented run (or cache if you want—your call)
        if use_cache and dump_pages_dir is None:
            cache.set(books)

        return books

    def _get_genres_pagination(self, page: int) -> str:
        """Fetch genres with pagination from Goodreads."""
        url = f"{self.BASE_URL}/genres/list?page={page}"
        logger.debug("GET request to: %s", url)
        return get_request(url)

    def _extract_genres_from_soup(self, soup) -> list:
        """Extract genres from BeautifulSoup object."""
        genres_text = []
        shelf_stats = soup.find_all("div", class_="shelfStat")

        for shelf_stat in shelf_stats:
            genre_link = shelf_stat.find("a", class_="mediumText actionLinkLite")
            if genre_link:
                genre_text = genre_link.text.strip()
                if all(32 <= ord(c) <= 126 for c in genre_text):
                    genres_text.append(genre_text)

        return genres_text

    def _get_books_for_genre_pagination(self, genre: str, page: int) -> str:
        """Fetch books for a genre with pagination from Goodreads."""
        url = f"{self.BASE_URL}/shelf/show/{genre}?page={page}"
        logger.debug("GET request to: %s", url)
        return get_request(url)

    def _extract_books_from_soup(self, soup) -> list:
        """Extract books from BeautifulSoup object."""
        books = []
        book_elements = soup.find_all("div", class_="elementList")

        for book_element in book_elements:
            title = ""
            book_url = ""
            compressed_img_url = ""
            author = ""
            avg_rating = 0.0
            total_ratings = 0
            published_year = 0

            title_elem = book_element.find("a", class_="bookTitle")
            if title_elem:
                title = title_elem.text.strip()
                href = (title_elem.get("href") or "").strip()
                if href:
                    # store absolute-ish path; caller can prepend BASE_URL if desired
                    book_url = href

            author_elem = book_element.find("a", class_="authorName")
            if author_elem:
                author = author_elem.text.strip()

            img_elem = book_element.find("img")
            if img_elem and img_elem.has_attr("src"):
                compressed_img_url = img_elem["src"].strip()

            rating_elem = book_element.find("span", class_="greyText smallText")
            if rating_elem:
                rating_text = rating_elem.text.strip()
                try:
                    avg_match = RATING_RE.search(rating_text)
                    count_match = RATINGS_COUNT_RE.search(rating_text)
                    if avg_match:
                        avg_rating = float(avg_match.group(1))
                    if count_match:
                        total_ratings = int(
                            count_match.group(1).replace(",", "")
                        )
                except ValueError:
                    pass

            pub_elem = book_element.find("span", class_="greyText smallText")
            if pub_elem:
                pub_text = pub_elem.text.strip()
                year_match = PUBLISHED_YEAR_RE.search(pub_text)
                if year_match:
                    try:
                        published_year = int(year_match.group(1))
                    except ValueError:
                        pass

            books.append(
                {
                    "title": title,
                    "book_url": book_url,
                    "author": author,
                    "compressed_img_url": compressed_img_url,
                    "avg_rating": avg_rating,
                    "total_ratings": total_ratings,
                    "published_year": published_year,
                }
            )

        return books

    def _get_next_page_href(self, soup) -> str | None:
        """Return href for a usable 'next page' link, else None.

        Goodreads pagination markup varies across pages. This checks the most
        common patterns and filters out disabled links.
        """
        # Prefer rel=next when present
        next_link = soup.select_one('a[rel="next"]')

        # Fallback to Goodreads' common next_page class
        if next_link is None:
            next_link = soup.select_one("a.next_page")

        # Extra fallback: sometimes 'next' is inside .pagination
        if next_link is None:
            next_link = soup.select_one(
                ".pagination a.next_page"
            ) or soup.select_one(".pagination a[rel='next']")

        if next_link is None:
            return None

        # Disabled checks (multiple variants seen)
        classes = set(next_link.get("class", []) or [])
        if "disabled" in classes:
            return None

        aria_disabled = (next_link.get("aria-disabled") or "").strip().lower()
        if aria_disabled == "true":
            return None

        # Some pages set disabled via parent <span class="next_page disabled">
        parent = next_link.parent
        if parent is not None:
            parent_classes = set(parent.get("class", []) or [])
            if "disabled" in parent_classes and "next_page" in parent_classes:
                return None

        href = (next_link.get("href") or "").strip()
        return href or None
