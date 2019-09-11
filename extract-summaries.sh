#!/usr/bin/env bash

set -eux

PYTHONHOME=${PYTHONHOME:-/c/Python27}

app=$1
[ -z "$app" ] && echo "Usage: $(basename "$0") application [prefix]" && exit 1

# Example:
# (Doc|EJB|Facade|Endpoint|web.struts|struts.action)
# ^((?!Scheduler).)*(Doc|Facade|Endpoint)

appPrefix=${2:-""}

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
            "modules/$source/calls.txt" \
            "modules/$source/methods.txt" \
            "modules/$target/methods.txt" \
            "$sourcePrefix" \
            "$targetPrefix" \
            > "$summaryFile"
        ! grep -q "###" "$summaryFile" && rm "$summaryFile"
    fi

    echo "Extracted call chains from $source to $target."
}

extract "$app" foo "$appPrefix" "(Doc|Gd)" &
extract "$app" bar "$appPrefix" "" &

for job in $(jobs -p)
do
    wait "$job" || echo "$job failed!"
done
