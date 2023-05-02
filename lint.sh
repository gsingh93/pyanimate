#!/usr/bin/env bash

set -x
set -e

LINT_FILES="src/pyanimate tests examples"

pylint ${LINT_FILES} || true
isort --check-only --diff ${LINT_FILES}
black --check --diff ${LINT_FILES}
flake8 --show-source ${LINT_FILES}
mypy --enable-incomplete-feature=TypeVarTuple ${LINT_FILES} || true
pyright ${LINT_FILES} || true
