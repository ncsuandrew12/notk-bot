#!/bin/bash

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
source "${DIR}/common.bash"

ERR_NOT_READY=10

target=""

argCnt=0
while (( "$#" )); do
    case "$1" in
        -*|--*=) # unsupported flags
            >&2 echo "ERROR: Unsupported parameter $1"
            exit $ERR_BAD_PARAMETER
            ;;
        *) # preserve positional arguments
            if [ $argCnt -eq 0 ]; then
                target="$1"
            else
                >&2 echo "ERROR: Unexpected argument $1"
                exit $ERR_BAD_ARGUMENT
            fi
            argCnt=$((argCnt+1))
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
    productionLocal)
        production=1
        ;;
    *)
        >&2 echo "ERROR: Invalid target: $target"
        exit $ERR_BAD_ARGUMENT
        ;;
esac

deploymentJson=$(jq -r ".${target}" ${ROOT_DIR}/bin/config.json)
targetDir=/home/`whoami`/$(jq -r ".dir" <<< $deploymentJson)

tag=`git tag --points-at HEAD`

sshfsDeployment=0
if [ $(jq -r ".deployMethod" <<< $deploymentJson) -eq "sshfs" ]; then
    sshfsDeployment=1
fi

if [[ `echo "$tag" | wc -w` -eq 0 ]]; then
    if [ $production -eq 1 ]; then
        >&2 echo "ERROR: The current commit is not tagged."
        exit $ERR_NOT_READY
    else
        tag=`head -1 ${ROOT_DIR}/VERSION`
    fi
fi

if [[ -e $targetDir ]]; then
    if [ $production -eq 0 ]; then
        echo "Deleting log directory if it exists."
        rm -rf $targetDir/log
    fi
else
    mkdir -p $targetDir
    if [ $sshfsDeployment -eq 1 ]; then
        sshfs -p $(jq -r ".port" <<< $deploymentJson) `whoami`@$(jq -r ".host" <<< $deploymentJson) $targetDir
    fi
fi

echo "Deploying to $target."

cp -vf ${ROOT_DIR}/releases/${tag}/RELEASE_NOTES ${targetDir}/
echo ${tag} > ${targetDir}/VERSION

cp -vf ${ROOT_DIR}/src/*.py ${targetDir}/

mkdir -p ${targetDir}/cfg/
cp -rvf ${ROOT_DIR}/cfg/$target/* ${targetDir}/cfg/
if [ $sshfsDeployment -eq 1 ]; then
    cp -vf ${ROOT_DIR}/cfg/$target/requirements.txt ${targetDir}/
fi

echo "Deployed to $target!"
