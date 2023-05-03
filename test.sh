#!/usr/bin/env bash

FILTER=${1:-""}
if [ "$FILTER" != "" ]; then
    shift
fi

pytest -v -l -k "$FILTER" --pyright-dir tests/typesafety tests $@
