#!/bin/bash

# Single-digit error codes are reserved for common error codes.
ERR_BAD_PARAMETER=1
ERR_BAD_ARGUMENT=2
ERR_MISSING_PARAMETER=3

ROOT_DIR="$( cd "$DIR" && cd .. && pwd )"

cd "$DIR"
