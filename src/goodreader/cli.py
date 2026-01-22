"""Command-line interface for Goodreader."""

import argparse
from goodreader.commands import search, genres, genre, author, isbn

def main() -> None:
    parser = argparse.ArgumentParser(description="Goodreader Command Line Interface")
    subparsers = parser.add_subparsers(dest='command')

    # Search command
    search_parser = subparsers.add_parser('search', help='Search for items by keyword')
    search_parser.add_argument('keyword', type=str, help='Keyword to search for')

    # Genres command
    subparsers.add_parser('genres', help='List all available genres')

    # Genre command
    genre_parser = subparsers.add_parser('genre', help='Get details about a specific genre')
    genre_parser.add_argument('keyword', type=str, help='Keyword for the genre')

    # Author command
    author_parser = subparsers.add_parser('author', help='Search for items by author')
    author_parser.add_argument('keyword', type=str, help='Author name or keyword')

    # ISBN command
    isbn_parser = subparsers.add_parser('isbn', help='Retrieve information based on ISBN')
    isbn_parser.add_argument('isbn_id', type=str, help='ISBN ID to look up')

    args = parser.parse_args()

    if args.command == 'search':
        search.execute(args.keyword)
    elif args.command == 'genres':
        genres.execute()
    elif args.command == 'genre':
        genre.execute(args.keyword)
    elif args.command == 'author':
        author.execute(args.keyword)
    elif args.command == 'isbn':
        isbn.execute(args.isbn_id)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()