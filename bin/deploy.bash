#!/bin/bash

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
source "${DIR}/common.bash"

ERR_NOT_READY=10

target=""
release=""

argCnt=0
while (( "$#" )); do
    case "$1" in
        -t|--target)
            if [ -n "$2" ] && [ ${2:0:1} != "-" ]; then
                target=$2
                shift 2
            else
                >&2 echo "ERROR: Argument for $1 is missing"
                exit ${ERR_BAD_ARGUMENT}
            fi
            ;;
        -r|--release)
            if [ -n "$2" ] && [ ${2:0:1} != "-" ]; then
                release=$2
                shift 2
            else
                >&2 echo "ERROR: Argument for $1 is missing"
                exit ${ERR_BAD_ARGUMENT}
            fi
            ;;
        *)
            >&2 echo "ERROR: Unsupported parameter $1"
            exit $ERR_BAD_PARAMETER
            ;;
    esac
done

production=0
case "${target}" in
    test)
        ;;
    production)
        production=1
        ;;
    productionLocal)
        production=1
        ;;
    *)
        >&2 echo "ERROR: Invalid target: ${target}"
        exit ${ERR_BAD_ARGUMENT}
        ;;
esac

sourceDir="${ROOT_DIR}"
if [ ${production} -eq 1 ]; then
    if [ -n ${release} ]; then
        >&2 echo "ERROR: Must specify release when deploying to production."
        exit ${ERR_MISSING_PARAMETER}
    fi
    cd /tmp
    sourceDir="notk-src-"$(cat /dev/urandom | tr -dc 'a-zA-Z0-9' | fold -w 32 | head -n 1)
    git clone git@github.com:ncsuandrew12/notk-bot.git ${sourceDir}
    sourceDir=/tmp/${sourceDir}
    cd ${sourceDir}
    if [ ${release} -eq "latest" ]; then
        release=`git tag | tail -1` # TODO Will not work starting with release 10.0 or 0.10
    fi
    git checkout ${release}
fi

deploymentJson=$(jq -r "." ${sourceDir}/cfg/${target}/deploy.json)
targetDir=/home/`whoami`/$(jq -r ".dir" <<< ${deploymentJson})

tag=`git tag --points-at HEAD`

sshfsDeployment=0
deployMethod=$(jq -r ".deployMethod" <<< ${deploymentJson})
if [ -n ${deployMethod} & ${deployMethod} -eq "sshfs" ]; then
    sshfsDeployment=1
fi

if [[ `echo "${tag}" | wc -w` -eq 0 ]]; then
    if [ ${production} -eq 1 ]; then
        >&2 echo "ERROR: The current commit is not tagged."
        exit $ERR_NOT_READY
    else
        pastHead=0
        while [[ `echo "${tag}" | wc -w` -eq 0 || ! ${tag} =~ ^[0-9]+\.[0-9]+$ ]]; do
            pastHead=$((pastHead+1))
            tag=`git tag --points-at HEAD~${pastHead}`
        done
    fi
fi

if [[ ${production} -eq 1 && ${tag} -ne ${release} ]]; then
    >&2 echo "ERROR: git label (${tag}) != release target (${release})"
    exit ${ERR_BAD_ARGUMENT}
fi

if [[ -e ${targetDir} ]]; then
    if [ ${production} -eq 0 ]; then
        echo "Deleting log directory if it exists."
        rm -rf ${targetDir}/log
    fi
else
    mkdir -p ${targetDir}
    if [ ${sshfsDeployment} -eq 1 ]; then
        sshfs -p $(jq -r ".port" <<< ${deploymentJson}) `whoami`@$(jq -r ".host" <<< ${deploymentJson}) ${targetDir}
    fi
fi

echo "Deploying to ${target}."

cp -vf ${sourceDir}/releases/${tag}/RELEASE_NOTES ${targetDir}/
echo ${tag} > ${targetDir}/VERSION

cp -vf ${sourceDir}/src/*.py ${targetDir}/

mkdir -p ${targetDir}/cfg/
cp -rvf ${sourceDir}/cfg/${target}/* ${targetDir}/cfg/
if [ ${sshfsDeployment} -eq 1 ]; then
    cp -vf ${sourceDir}/cfg/${target}/requirements.txt ${targetDir}/
fi

echo "Deployed to ${target}!"
