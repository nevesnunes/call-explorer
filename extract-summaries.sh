#!/usr/bin/env bash

set -eux

PYTHONHOME=${PYTHONHOME:-/c/Python27}

app=$1
[ -z "$app" ] && echo "Usage: $(basename "$0") application [sourcePrefix] [targetPrefix]" && exit 1

# Example:
# (Doc|EJB|Facade|Endpoint|web.struts|struts.action)
# ^((?!Scheduler).)*(Doc|Facade|Endpoint)
sourcePrefix=${2:-""}
targetPrefix=${3:-""}

true > sum-errors.txt
mkdir -p ./modules

function extract {
    source=$1
    target=$2
    sourcePrefix=$3
    targetPrefix=$4
    [ "$source" == "$target" ] && return

    echo "Checking call chains from $source to $target."

    summaryFile="$source-$target-summary.md"
    countSummaryFiles=$(find . -iname "$source-*-summary.md" | wc -l)
    if [ "$countSummaryFiles" -eq 0 ]; then
        "$PYTHONHOME"/python sum.py \
            "modules/$source/calls.json" \
            "modules/$source/methods.txt" \
            "modules/$target/methods.txt" \
            "$sourcePrefix" \
            "$targetPrefix" \
            > "$summaryFile"
        ! grep -q "###" "$summaryFile" && rm "$summaryFile"
    fi

    echo "Extracted call chains from $source to $target."
}

# Set as many calls as target modules to run against
extract "$app" foo "$sourcePrefix" "$targetPrefix" &
extract "$app" bar "$sourcePrefix" "$targetPrefix" &
extract "$app" baz "$sourcePrefix" "$targetPrefix" &

for job in $(jobs -p)
do
    wait "$job" || echo "$job failed!"
done
