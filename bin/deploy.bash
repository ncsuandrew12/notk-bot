#!/bin/bash

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
source "${DIR}/common.bash"

target=""

argCnt=0
while (( "$#" )); do
    case "$1" in
        -*|--*=) # unsupported flags
            >&2 echo "ERROR: Unsupported parameter $1"
            exit 1
            ;;
        *) # preserve positional arguments
            if [ $argCnt -eq 0 ]; then
                target="$1"
            else
                >&2 echo "ERROR: Unexpected argument $1"
                exit 2
            fi
            $((argCnt+1))
            shift
            ;;
    esac
done

production=0
case "$target" in
    test)
        ;;
    production)
        production=1
        ;;
    *)
        >&2 echo "ERROR: Invalid target: $target"
        exit 3
        ;;
esac

deploymentJson=$(jq -r ".${target}" ${ROOT_DIR}/bin/config.json)
targetDir=/home/`whoami`/$(jq -r ".dir" <<< $deploymentJson)

tag=`git tag --points-at HEAD`

if [ $production -eq 1 ] && [[ `echo "$tag" | wc -w` -eq 0 ]]; then
    >&2 echo "ERROR: The current commit is not tagged."
    exit 4
fi

if [[ ! -e $targetDir ]]; then
    mkdir -p $targetDir
    if [ $production -eq 1 ]; then
        mkdir -p $targetDir
        sshfs -p $(jq -r ".port" <<< $deploymentJson) `whoami`@$(jq -r ".host" <<< $deploymentJson) $targetDir
    fi
fi

echo "Deploying to $target."

cp -vf ${ROOT_DIR}/RELEASE_NOTES ${targetDir}/
cp -vf ${ROOT_DIR}/VERSION ${targetDir}/

cp -vf ${ROOT_DIR}/src/*.py ${targetDir}/

mkdir -p ${targetDir}/cfg/
cp -rvf ${ROOT_DIR}/cfg/$target/* ${targetDir}/cfg/

echo "Deployed to $target!"

${ROOT_DIR}/bin/startServer${target}.bash