#!/bin/bash
set -e
shopt -s extglob


#
# Quiet versions of pushd/popd builtins
#
function pushd {
    command pushd "$@" > /dev/null
}
function popd {
    command popd "$@" > /dev/null
}


#
# Normalize project name
#
# Arguments:
#   $1     - Raw project name
#
function normalize {
    echo $1 | sed -E -e 's/[-_.]+/-/g' | tr '[:upper:]' '[:lower:]'
}


#
# Calculate the sha256 checksum of a file
#
# Arguments:
#   $1     - Path to file
#
function calculate_sha256 {
    sha256sum -b $1 | cut -d' ' -f1
}


#
# Collect a wheel into the output directory
#
# Arguments:
#   $1     - Path to wheel file to be collected
#
function collect_wheel {
    local whlpath=$1
    local whlname=$(basename $whlpath)
    local meta=$(unzip -Z -1 $whlpath | grep .dist-info/METADATA$)
    local proj=$(normalize ${meta%-+([0-9]|.).dist-info/METADATA})

    mkdir -p $proj
    pushd $proj

    cp $whlpath $whlname
    unzip -p $whlpath $meta > $whlname.metadata

    popd
}


#
# Write the root index page
#
# Arguments:
#   $1..n  - Project names to include in index
#
function write_root_index {
    echo "<!DOCTYPE html>"
    echo "<html>"
    echo "  <head>"
    echo "    <meta name=\"pypi:repository-version\" content=\"1.0\">"
    echo "  </head>"
    echo "  <body>"

    for project in "$@"; do
        echo "    <a href=\"./$project/\">$project</a><br />"
    done

    echo "  </body>"
    echo "</html>"
}


#
# Write index page for a particular project
#
# Arguments:
#   $1     - Project name
#   $2..n  - Wheels available for project
#
function write_project_index {
    local name=$1
    shift

    echo "<!DOCTYPE html>"
    echo "<html>"
    echo "  <head>"
    echo "    <meta name=\"pypi:repository-version\" content=\"1.0\">"
    echo "    <title>Links for $name</title>"
    echo "  </head>"
    echo "  <body>"
    echo "    <h1>Links for $name</h1>"

    for whl in "$@"; do
        local whlhash=$(calculate_sha256 $whl)
        local metahash=$(calculate_sha256 $whl.metadata)

        echo -n "    <a href=\"$whl#sha256=$whlhash\""
        echo " data-dist-info-metadata=\"sha256=$metahash\">$whl</a><br />"
    done

    echo "    </body>"
    echo "</html>"
}


#
# Make package repository
#
# Arguments:
#  $1      - Directory containing wheels
#  $2      - Directory to write output into
#
function main {
    local whldir=$(realpath $1)
    local outdir=$(realpath $2)/simple

    if [ -e $outdir ]; then
        echo "Output directory exists: $outdir"
        exit 1
    fi
    mkdir -p $outdir
    cd $outdir

    echo "Collecting wheels"
    for whl in $(find $whldir -type f -name "*.whl"); do
        echo "  $whlname"
        collect_wheel $whl
    done

    echo "Writing root index"
    local projects=(*)
    write_root_index ${projects[@]} > index.html

    for project in ${projects[@]}; do
        echo "Writing project index [$project]"
        pushd $project
        write_project_index $project *.whl > index.html
        popd
    done

    echo "Done."
}


#
# Usage:
#   $ ./make-package-repository WHLDIR OUTDIR
#
main "$@"
