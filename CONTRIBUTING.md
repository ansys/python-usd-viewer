# Contribute

Overall guidance on contributing to a PyAnsys library appears in the
[Contributing] topic in the *PyAnsys developer's guide*. Ensure that you
are thoroughly familiar with this guide before attempting to contribute to
ansys-tools-usdviewer.

The following contribution information is specific to the Python USD Viewer.

[Contributing]: https://dev.docs.pyansys.com/how-to/contributing.html

## Clone the repository

To clone and install the latest Python USD Viewer release in development mode, run
these commands:

```bash
git clone https://github.com/ansys/python-usd-viewer/
cd python-usd-viewer
pip install uv  # if uv is not already installed
uv sync --group dev
```

## Adhere to code style

The Python USD Viewer follows the PEP8 standard as outlined in PEP 8 in the *PyAnsys developer’s guide* and implements style checking using pre-commit.
To ensure your code meets minimum code styling standards, run these commands:

```bash
uv pip install pre-commit
pre-commit run --all-files
```

You can also install this as a pre-commit hook by running this command:

```bash
pre-commit install
```

## Run the tests

Prior to running the tests, you must run this command to install the test dependencies:

```bash
uv sync --group tests
```

To run the tests, navigate to the root directory of the repository and run this command:

```bash
uv run pytest
```


## Build the documentation

Prior to building the documentation, you must run this command to install the documentation dependencies:

```bash
uv sync --group doc
```

To build the documentation, run the following commands:

```bash
cd doc

# On Linux
uv run make html

# On Windows
uv run ./make.bat html
```

The documentation is built in the `docs/_build/html` directory.
