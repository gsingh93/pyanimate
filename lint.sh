#!/usr/bin/env bash

set -x
set -e

LINT_FILES="src/pyanimate tests examples"

ruff check --fix --show-source ${LINT_FILES}
# mypy ${LINT_FILES} || true

# We use tests/*.py here to exclude the typesafety directory. We can't just
# exclude this directory in the config because then it won't be checked at all
# by pytest-pyright
pyright src/pyanimate examples tests/*.py

isort --check-only --diff ${LINT_FILES}
black --check --diff ${LINT_FILES}

PYTHONPATH=$(pwd) pylint --load-plugins assert_checker,assign_dim_in_prepare ${LINT_FILES} || true
