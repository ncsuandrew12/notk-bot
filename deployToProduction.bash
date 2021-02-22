#!/bin/bash

TARGET="/production/notk-bot"

tag=`git tag --points-at HEAD`

if [[ `echo "$tag" | wc -w` -eq 0 ]]; then
    >&2 echo "ERROR: The current commit is not tagged."
    exit 1
fi

echo "Deploying to production"

cp -vf main.py "${TARGET}/"
cp -vf discord.token "${TARGET}/"
cp -vf config.json "${TARGET}/"

echo "Deployed to production!"
