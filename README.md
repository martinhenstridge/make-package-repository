# make-package-repository

A bash script to produce a static Python package repository from a directory containing [wheel](https://peps.python.org/pep-0427/) files. Inspired by [`simple503`](https://github.com/repo-helper/simple503).

The generated package repository is compatible with the following:

* [PEP 503](https://peps.python.org/pep-0503/) - Simple Repository API
* [PEP 629](https://peps.python.org/pep-0629/) - Versioning PyPI’s Simple API
* [PEP 658](https://peps.python.org/pep-0658/) - Serve Distribution Metadata in the Simple Repository API

## Usage

Run the script as follows:

```bash
./make-package-repository WHLDIR OUTDIR
```

where `WHLDIR` is a directory containing `.whl` files and `OUTDIR` is where the package repository will be created (under the `/simple` subdirectory, matching the convention set by PyPI).

Next, spawn an HTTP server at the root of the package repository. For example:

```bash
python3 -m http.server -d OUTDIR
```

The package repository is now ready for use, for example as an extra index to `pip`:

```bash
pip install foobar --extra-index-url http://localhost:8000/simple
```
