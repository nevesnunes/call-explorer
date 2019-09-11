#!/bin/sh

set -eux

PYTHONHOME=${PYTHONHOME:-/c/Python27}

source=$1
target=$2
#"../modules/$source/calls.json" \
"PYTHONHOME"/python sum.py \
    "./modules/$source/calls.txt" \
    "./modules/$source/methods.txt" \
    "./modules/$target/methods.txt" \
    "(Doc|Facade|Endpoint)" #\
    #> summary.md
