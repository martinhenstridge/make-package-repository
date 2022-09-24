#!/usr/bin/env python3
import hashlib
import logging
import pathlib
import re
import shutil
import sys
import zipfile

logging.basicConfig(level=logging.INFO, format="%(message)s")


def normalize(name):
    return re.sub(r"[-_.]+", "-", name).lower()


def calculate_sha256(path):
    h = hashlib.sha256()

    with open(path, "rb") as f:
        while True:
            chunk = f.read(4096)
            if not chunk:
                break
            h.update(chunk)

    return h.hexdigest()


def parse_wheel_project_version(path):
    m = re.match(
        r"([A-Za-z0-9](?:[A-Za-z0-9._]*[A-Za-z0-9])?)-([A-Za-z0-9_.!+]+)-",
        path.name,
    )
    if not m:
        raise Exception("Invalid wheel name", path.name)

    return m[1], m[2]


def collect_wheel(outdir, whl):
    project, version = parse_wheel_project_version(whl)

    with zipfile.ZipFile(whl) as z:
        metadata = z.read(f"{project}-{version}.dist-info/METADATA")

    project_dir = pathlib.Path(outdir / normalize(project))
    project_dir.mkdir(exist_ok=True)

    shutil.copyfile(whl, project_dir / whl.name)
    (project_dir / f"{whl.name}.metadata").write_bytes(metadata)


ROOT_INDEX_PREAMBLE = """\
<!DOCTYPE html>
<html>
  <head>
    <meta name="pypi:repository-version" content="1.0">
  </head>
  <body>
"""
ROOT_INDEX_POSTAMBLE = """\
  </body>
</html>
"""


def write_root_index(index, projects):
    index.write(ROOT_INDEX_PREAMBLE)
    for p in projects:
        index.write(f'    <a href="{p.name}/">{p.name}</a>')
        index.write("<br />\n")
    index.write(ROOT_INDEX_POSTAMBLE)


PROJECT_INDEX_PREAMBLE = """\
<!DOCTYPE html>
<html>
  <head>
    <meta name="pypi:repository-version" content="1.0">
    <title>Links for {0}</title>
  </head>
  <body>
    <h1>Links for {0}</h1>
"""
PROJECT_INDEX_POSTAMBLE = """\
    </body>
</html>
"""


def write_project_index(index, project):
    index.write(PROJECT_INDEX_PREAMBLE.format(project.name))
    for whl in project.glob("*.whl"):
        whlhash = calculate_sha256(project / whl)
        metahash = calculate_sha256(project / f"{whl.name}.metadata")
        index.write(
            f'    <a href="{whl.name}#sha256={whlhash}" '
            f'data-dist-info-metadata="sha256={metahash}">{whl.name}</a>'
        )
        index.write("<br />\n")
    index.write(PROJECT_INDEX_POSTAMBLE)


def main(whldir_in, outdir_in):
    whldir = pathlib.Path(whldir_in).resolve()
    outdir = pathlib.Path(outdir_in).resolve() / "simple"

    outdir.mkdir(parents=True)

    logging.info("Collecting wheels")
    for whl in whldir.rglob("*.whl"):
        logging.info("  %s", whl.name)
        collect_wheel(outdir, whldir / whl)

    logging.info("Writing root index")
    projects = sorted(outdir.iterdir())
    with open(outdir / "index.html", "w") as f:
        write_root_index(f, projects)

    for project in projects:
        logging.info("Writing project index [%s]", project.name)
        with open(project / "index.html", "w") as f:
            write_project_index(f, project)

    logging.info("Done.")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
