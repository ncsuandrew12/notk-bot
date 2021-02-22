#!/bin/bash

set -x

git add *

set -e

git diff --cached > diff.diff

git status
