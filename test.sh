#!/usr/bin/env bash

set -x

export PYTEST_ADDOPTS="--showlocals -v -s"

FILTER=${1:-""}
if [ "$FILTER" != "" ]; then
    PYTEST_ADDOPTS="-k $FILTER $PYTEST_ADDOPTS"
    shift
fi

if [[ $CI == true ]]; then
    PYTEST_ADDOPTS="--cov $PYTEST_ADDOPTS"
fi
pytest --pyright-dir tests/typesafety tests $@
