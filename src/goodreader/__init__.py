"""Initialize the goodreader package."""

import logging


try:
    from importlib.metadata import PackageNotFoundError, version
except ImportError:  # pragma: no cover
    from importlib_metadata import (  # type: ignore[assignment]
        PackageNotFoundError,
        version,
    )


try:
    __version__ = version(__name__)
except PackageNotFoundError:  # pragma: no cover
    __version__ = "unknown"


# Basic configuration with debug level
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

# Or configure specifically for goodreader module
logging.getLogger("goodreader").setLevel(logging.DEBUG)
logging.getLogger("charset_normalizer").setLevel(logging.WARNING)
