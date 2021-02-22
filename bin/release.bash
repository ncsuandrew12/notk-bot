#!/bin/bash

set -e

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
source "${DIR}/common.bash"

cd "${ROOT_DIR}"

dryRun=0

if [ "$1" == "--dry-run" ]; then
    dryRun=1
fi

majorRelease=0

if [[ `git status --short | wc -l` -ne 0 ]]; then
    >&2 echo "ERROR: Uncommitted files:"
    git status
    exit 1
fi;

if [ $dryRun -eq 0 ]; then
    echo "Pushing changes."
    git push
fi

if [[ ! -f release_notes ]]; then
    >&2 echo "Missing release notes!"
    exit 3
fi

major=0
minor=0;
if [ `git tag --list | wc -l` -gt 0 ]; then
    # TODO Generalize to any number of digits
    latestVersion=`git tag --list | sed -r 's/\.([0-9])$/.0\1/g' | sed -r 's/\.([0-9][0-9])$/.0\1/g' | sort | tail -1`
    latestMajor=$(sed s'/\.[^.]*$//' <<< $latestVersion)
    latestMinor=$(sed s'/[^.]*\.//' <<< $latestVersion)
    latestMajor=$(sed -r 's/^0+([1-9][0-9]*)/\1/' <<< $latestMajor)
    latestMinor=$(sed -r 's/^0+([1-9][0-9]*)/\1/' <<< $latestMinor)

    major=$((latestMajor))
    if [ $majorRelease -eq 1 ]; then
        major=$((major+1))
        minor=0
    else
        minor=$((latestMinor+1))
    fi
fi;

newVersion="${major}.${minor}"

tagLabel="${newVersion}"

read -p "Release $tagLabel? [y/N]: " doRelease
doRelease=$(tr '[:upper:]' '[:lower:]' <<< $doRelease)
if [[ "$doRelease" != "y" ]]; then
    >&2 echo "Release cancelled!"
    exit 2
fi
if [ $dryRun -eq 0 ]; then
    echo "Creating release branch"
    if [ $majorRelease -eq 1 ]; then
        git checkout -b release/${major}
    fi

    echo "Creating release directory."
    mkdir -p releases/${tagLabel}

    echo "Moving release notes."
    cp release_notes Release_Notes.md
    mv release_notes releases/${tagLabel}/Release_Notes.md

    echo "Committing changes."
    git add releases/${tagLabel}
    git commit -m "Prepping release: $tagLabel"
    git push

    echo "Labelling release."
    git tag -a "$tagLabel" -m "Tagging $tagLabel"

    echo "Pushing tags."
    git push --tags
fi
