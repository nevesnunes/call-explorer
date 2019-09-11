#!/usr/bin/env bash

set -eux

target=$(realpath "$1")
package_included="$2"
main_class="$3"

# NOTE: Skipping jars inside wars
while read -r i; do
    if ! [ -d "$i.extracted" ]; then
        unzip -d "$i.extracted" "$i"
    fi
    if ! [ -d "$i.jar" ]; then
        cp "$i" "$i.jar"
    fi
done <<< "$(find "$target" -iname '*war')"

classpath="$(find "$JAVA_HOME" -iname "*rt.jar" | grep "lib/rt.jar" | head -n1)"
while read -r i; do
  classpath+=":$i"
done <<< "$(find "$target" -iname '*jar')"

if ! [ -f "$target/calls-dynamic.txt" ]; then
    java \
      -Xbootclasspath:"$classpath" \
      -javaagent:./lib/javacg-0.1-SNAPSHOT-dycg-agent.jar="incl=$package_included.*;" \
      -classpath "$target/"*jar "$main_class" > "$target/calls-dynamic.txt"
fi
