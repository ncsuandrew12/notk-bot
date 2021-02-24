#!/bin/bash

set -x
set -e

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
source "${DIR}/common.bash"

cd "${ROOT_DIR}"

dryRun=0
majorRelease=0

version=""

argCnt=0
while (( "$#" )); do
    case "$1" in
        -d|--dry-run)
            dryRun=1
            shift
            ;;
        -m|--major-release)
            majorRelease=1
            shift
            ;;
        # -e|--version)
        #     if [ -n "$2" ] && [ ${2:0:1} != "-" ]; then
        #     MY_FLAG_ARG=$2
        #     shift 2
        #     else
        #     >&2 echo "ERROR: Argument for $1 is missing"
        #     exit 1
        #     fi
        #     ;;
        -*|--*=) # unsupported flags
            >&2 echo "ERROR: Unsupported parameter $1"
            exit 1
            ;;
        *) # preserve positional arguments
            if [ $argCnt -eq 0 ]; then
                version="$1"
            else
                >&2 echo "ERROR: Unexpected argument $1"
                exit 2
            fi
            $((argCnt+1))
            shift
            ;;
    esac
done

if [[ `git status --short | wc -l` -ne 0 ]]; then
    >&2 echo "ERROR: Uncommitted files:"
    git status
    exit 3
fi

if [ $dryRun -eq 0 ]; then
    echo "Pushing changes."
    git push
fi

if [[ ! -f RELEASE_NOTES ]]; then
    >&2 echo "Missing release notes!"
    exit 4
fi

major=-1
minor=0
if [[ $version =~ ^[0-9]+\.[0-9]+$ ]]; then
    major=$(sed -r 's/\..*$//' <<< $version)
    minor=$(sed -r 's/^.*\.//' <<< $version)
elif [ "$version" == "" ]; then
    if [ `git tag --list | wc -l` -gt 0 ]; then
        latestVersion=`git describe --abbrev=0`
        latestMajor=$(sed s'/\.[^.]*$//' <<< $latestVersion)
        latestMinor=$(sed s'/[^.]*\.//' <<< $latestVersion)
        latestMajor=$(sed -r 's/^0*([0-9]+)/\1/' <<< $latestMajor)
        latestMinor=$(sed -r 's/^0*([0-9]+)/\1/' <<< $latestMinor)

        major=$((latestMajor))
        minor=$((latestMinor))
    fi
else
    >&2 echo "ERROR: Invalid version string given: \'${version}\'"
    exit 5
fi

if [ $majorRelease -eq 1 ]; then
    major=$((major+1))
    minor=0
else
    minor=$((minor+1))
fi

newVersion="${major}.${minor}"

tagLabel="${newVersion}"

read -p "Release $tagLabel? [y/N]: " -n 1 doRelease
echo
doRelease=$(tr '[:upper:]' '[:lower:]' <<< $doRelease)
if [[ ! $doRelease =~ ^[Yy]$ ]]; then
    >&2 echo "Release cancelled!"
    exit 6
fi
if [ $dryRun -eq 0 ]; then
    echo "Creating release branch"
    if [ $majorRelease -eq 1 ]; then
        git checkout -b release/${major}
    fi

    echo "Creating release directory."
    mkdir -p releases/${tagLabel}

    echo "Copying release notes."
    cp RELEASE_NOTES releases/${tagLabel}/RELEASE_NOTES

    echo "Documenting version."
    echo ${tagLabel} > VERSION

    echo "Committing changes."
    git add releases/${tagLabel}
    git commit -m "Prepping release: $tagLabel"
    if [ $majorRelease -eq 1 ]; then
        git push --set-upstream origin release/${major}
    else
        git push
    fi

    echo "Labelling release."
    git tag -a "$tagLabel" -m "Tagging $tagLabel"

    echo "Pushing tags."
    git push --tags
fi
