#!/bin/sh
set -e
set -x
if git stat --short . | grep -Fq '.'
then
    echo "Working tree is dirty. Only update the changelog from a clean tree!"
    exit 1;
fi

poetry run gitchangelog ^1.3.4 HEAD > CHANGELOG.rst
git add CHANGELOG.rst
git commit --no-verify -m "@minor Update CHANGELOG.rst"
