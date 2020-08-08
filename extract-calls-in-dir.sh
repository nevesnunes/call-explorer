#!/usr/bin/env bash

set -eux

target=$(realpath "$1")

# NOTE: Skipping jars inside wars
while read -r i; do
  if [ -z "$i" ]; then
    continue
  fi
  if ! [ -d "$i.extracted" ]; then
    unzip -d "$i.extracted" "$i"
  fi
  if ! [ -d "$i.jar" ]; then
    cp "$i" "$i.jar"
  fi
done <<< "$(find "$target" -iname '*war')"

if ! [ -s "$target/calls.txt" ]; then
  java -jar ./lib/javacg-0.1-SNAPSHOT-static.jar \
    "$target/"*jar > "$target/calls.txt"
fi
