#!/bin/sh
mypy --silent-imports --disallow-untyped-calls --disallow-untyped-defs --check-untyped-defs --warn-incomplete-stub --warn-redundant-casts --warn-unused-ignores --strict-optional sensors/
