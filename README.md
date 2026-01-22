<div align="center">

# Goodreader

A simple project to be able to search 
and lookup books from Goodreads.

<br />

[![Tests](https://github.com/xransum/goodreader/workflows/Tests/badge.svg)][tests]
[![Codecov](https://codecov.io/gh/xransum/goodreader/branch/main/graph/badge.svg)][codecov]
[![PyPI](https://img.shields.io/pypi/v/goodreader.svg)][pypi_]
[![Python Version](https://img.shields.io/pypi/pyversions/goodreader)][python version]

[![Python Black](https://img.shields.io/badge/code%20style-black-000000.svg?label=Style)](https://github.com/xransum/goodreader)
[![Read the documentation at https://goodreader.readthedocs.io/](https://img.shields.io/readthedocs/goodreader/latest.svg?label=Read%20the%20Docs)][read the docs]
[![Downloads](https://pepy.tech/badge/goodreader)](https://pepy.tech/project/goodreader)
[![License](https://img.shields.io/pypi/l/goodreader)][license]

</div>

## Installation

To install the Goodreader project, run this command in your terminal:

```bash
pip install goodreader
```

## Usage

Once installed, you can use the Goodreader command-line interface with the following commands:

1. **Search for items by keyword:**
   ```bash
   goodreader search <keyword>
   ```

2. **List all available genres:**
   ```bash
   goodreader genres
   ```

3. **Get details about a specific genre:**
   ```bash
   goodreader genre <keyword>
   ```

4. **Search for items by author:**
   ```bash
   goodreader author <keyword>
   ```

5. **Retrieve information based on ISBN:**
   ```bash
   goodreader isbn <isbn-id>
   ```

For usage instructions, please refer to the [Usage][usage] documentation.

## Reference

For a complete list of available functions and classes, please refer to the
[Reference][reference] documentation.

## Contributing

Contributions are very welcome. To learn more, see the [Contributor
Guide][contributing].

## License

Distributed under the terms of the [MIT license][license], _goodreader_ is free
and open source software.

## Issues

If you encounter any problems, please [file an issue] along with a detailed
description.

## Credits

This project was built off of the sweat and tears of the the bad actors it was
built to fight.

<!-- github-only -->

[pypi_]: https://pypi.org/project/goodreader/
[python version]: https://pypi.org/project/goodreader
[read the docs]: https://goodreader.readthedocs.io/
[reference]: https://goodreader.readthedocs.io/en/latest/reference/
[usage]: https://goodreader.readthedocs.io/en/latest/
[tests]: https://github.com/xransum/goodreader/actions?workflow=Tests
[codecov]: https://app.codecov.io/gh/xransum/goodreader
[contributing]: ./CONTRIBUTING.md
[license]: ./LICENSE
