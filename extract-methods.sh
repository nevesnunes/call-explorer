#!/usr/bin/env bash

set -eux

PYTHONHOME=${PYTHONHOME:-/c/Python27}

parser_dir=$PWD
target=$(realpath "./modules")

while read -r i; do
    [ -f "$i/../methods.txt" ] && continue

    true > "$i/../methods.txt.accumulator"
    cd "$i"
    while read -r wsdl; do
    "$PYTHONHOME"/python "$parser_dir/parse-xml.py" \
        "$wsdl" \
        'wsdl:operation' \
        'name' \
        >> "$i/../methods.txt.accumulator"
    "$PYTHONHOME"/python "$parser_dir/parse-xml.py" \
        "$wsdl" \
        'operation' \
        'name' \
        >> "$i/../methods.txt.accumulator"
    done <<< "$(find . -maxdepth 1 -type f -iname '*wsdl')"
    sort -u "$i/../methods.txt.accumulator" > "$i/../methods.txt"
    rm "$i/../methods.txt.accumulator"
done <<< "$(find "$target" -type d -iname '*wsdl')"
