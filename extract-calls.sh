#!/usr/bin/env bash

set -eux

target=$(realpath "./modules")

while read -r i; do
    if ! [ -d "$i.extracted" ]; then
        unzip -d "$i.extracted" "$i"
    fi
done <<< "$(find "$target" -iname '*ear')"

# NOTE: Skipping jars inside wars
while read -r i; do
    if ! [ -d "$i.extracted" ]; then
        unzip -d "$i.extracted" "$i"
    fi
    if ! [ -d "$i.jar" ]; then
        cp "$i" "$i.jar"
    fi
done <<< "$(find "$target" -iname '*war')"

for i in ./"$target"/*; do 
    if ! [ -f "$target/$i/calls.txt" ]; then
        java -jar ./lib/javacg-0.1-SNAPSHOT-static.jar \
            --source-path /c/eld4/modules/ \
            "$target/$i/$i.ear.extracted/"*jar > "$target/$i/calls.txt"
    fi
    # FIXME: When using sources the parser may not print results, check exceptions
    if [ "$(wc -l "$target/$i/calls.txt" | cut -d' ' -f1)" -eq 0 ]; then
        java -jar ./lib/javacg-0.1-SNAPSHOT-static.jar \
            "$target/$i/$i.ear.extracted/"*jar > "$target/$i/calls.txt"
    fi
done

while read -r i; do
    cd "$i"
    wsdl_dir="$i/../wsdl"
    if [ -d "$wsdl_dir" ]; then
        continue
    fi
    mkdir "$wsdl_dir"
    while read -r j; do
        while read -r wsdl; do
            if [ -n "$wsdl" ]; then
                basename=$(echo "$wsdl" | sed 's/.*\///g')
                unzip -cq "$j" "$wsdl" > "$wsdl_dir/$basename"
            fi
        done <<< "$(unzip -l "$j" | grep -iE 'wsdl$' | awk '{print $4}')"
    done <<< "$(find . -maxdepth 1 -iname '*jar')"
    if ! [ "$(ls -A "$wsdl_dir")" ]; then
        rmdir "$wsdl_dir"
    fi
done <<< "$(find "$target" -iname '*ear.extracted')"
