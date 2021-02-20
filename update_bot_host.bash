#!/bin/bash

HOST_MNT="/production/notk-bot/"

tag=`git tag --points-at HEAD`

if [[ `echo "$tag" | wc -w` -eq 0 ]]; then
    >&2 echo "ERROR: The current commit is not tagged."
    exit 1
fi

echo "Updating bot host with notk-bot "

cp -vf main.py "${HOST_MNT}"
cp -vf discord.token "${HOST_MNT}"
cp -vf config.json "${HOST_MNT}"