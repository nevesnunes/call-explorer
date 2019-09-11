#!/bin/sh

source=$1
target=$2
#"../modules/$source/calls.json" \
#PYTHONHOME=/c/Python27 /c/Python27/python -m cProfile -o profile.out sum.py \
PYTHONHOME=/c/Python27 /c/Python27/python sum.py \
    "./calls.json" \
    "../modules/$source/methods.txt" \
    "../modules/$target/methods.txt" \
    "(Doc|Gd)" \
    "" \
    "$source" \
    "$target" #\
    #> summary.md
