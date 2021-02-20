#!/bin/bash

HOST_MNT="/production/notk-bot/"

echo "Updating bot host"

cp -vf main.py "${HOST_MNT}"
cp -vf discord.token "${HOST_MNT}"
cp -vf config.json "${HOST_MNT}"