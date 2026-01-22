"""Wrapper API for Goodreads."""

import logging
import re

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
                # logger.debug(
                #     "Extracted %d genres from page %d", len(page_genres), page
                # )
                genres.extend(page_genres)

            # To know if there's more pages, the pagination button won't be disabled
            has_next = soup.select_one(".next_page:not(.disabled)")
            if not has_next:
                # logger.debug("No more pages found")
                break

            page += 1

        logger.info("Fetched total of %d genres", len(genres))
        cache.set(genres)
        return genres

    def _get_genres_pagination(self, page: int) -> str:
        """Fetch genres with pagination from Goodreads."""
        url = f"{self.BASE_URL}/genres/list?page={page}"
        logger.debug("GET request to: %s", url)
        return get_request(url)

    def _extract_genres_from_soup(self, soup) -> list:
        """Extract genres from BeautifulSoup object."""
        genres_text = []
        shelf_stats = soup.find_all("div", class_="shelfStat")
        # logger.debug("Found %d shelf stats elements", len(shelf_stats))

        for shelf_stat in shelf_stats:
            genre_link = shelf_stat.find("a", class_="mediumText actionLinkLite")
            if genre_link:
                genre_text = genre_link.text.strip()

                # Goodreads pages seem to have genres with invalid chars which
                # breaks the URL when visiting them. So we ensure here to only
                # keep genres with printable ASCII characters.
                if all(32 <= ord(c) <= 126 for c in genre_text):
                    genres_text.append(genre_text)

        return genres_text

    def get_books_for_genre(self, genre: str) -> list:
        """Get list of books for a given genre from Goodreads."""
        logger.info("Fetching books for genre: %s", genre)
        books = []
        page = 1

        while True:
            logger.debug("Fetching books for genre '%s', page %d", genre, page)
            content = self._get_books_for_genre_pagination(genre, page)
            soup = soupify(content)

            page_books = self._extract_books_from_soup(soup)
            if page_books:
                # logger.debug("Extracted %d books from page %d", len(page_books), page)
                books.extend(page_books)

            # To know if there's more pages, the pagination button won't be disabled
            has_next = soup.select_one(".next_page:not(.disabled)")
            if not has_next:
                # logger.debug("No more pages found for genre '%s'", genre)
                break

            page += 1

        logger.info(
            "Fetched total of %d books for genre '%s'", len(books), genre
        )
        return books

    def _get_books_for_genre_pagination(self, genre: str, page: int) -> str:
        """Fetch books for a genre with pagination from Goodreads."""
        url = f"{self.BASE_URL}/shelf/show/{genre}?page={page}"
        logger.debug("GET request to: %s", url)
        return get_request(url)

    def _extract_books_from_soup(self, soup) -> list:
        """Extract books from BeautifulSoup object."""
        books = []
        book_elements = soup.find_all("div", class_="elementList")
        # logger.debug("Found %d book elements", len(book_elements))

        title: str = ""
        compressed_img_url: str = ""
        author: str = ""
        avg_rating: float = 0.0
        total_ratings: int = 0
        published_year: int = 0

        for book_element in book_elements:
            title_elem = book_element.find("a", class_="bookTitle")
            if title_elem:
                title = title_elem.text.strip()

            author_elem = book_element.find("a", class_="authorName")
            if author_elem:
                author = author_elem.text.strip()

            # a.leftAlignedImage > img
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
                    "author": author,
                    "compressed_img_url": compressed_img_url,
                    "avg_rating": avg_rating,
                    "total_ratings": total_ratings,
                    "published_year": published_year,
                }
            )

        return books
