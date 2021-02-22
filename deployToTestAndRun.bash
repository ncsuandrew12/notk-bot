#!/bin/bash

set -e

./deployToTest.bash

cd /test/notk-bot

python3 main.py
