#!/bin/bash

TARGET="/test/notk-bot"

echo "Deploying to test"

cp -vf main.py "${TARGET}/"
cp -vf discord-test.token "${TARGET}/discord.token"
cp -vf config-test.json "${TARGET}/config.json"

echo "Deployed to test!"
