#!/usr/bin/env python2

# -*- coding: utf-8 -*-

import json
import os
import re
import sys

if __name__ == "__main__":
    lines = []
    if not sys.stdin.isatty():
        for line in sys.stdin:
            lines.append(line.strip())
    else:
        filename = sys.argv[1]
        with open(filename) as f:
            lines = [x.strip() for x in f.readlines()] 

    chains = []
    edgeRegex = re.compile("^([^ ]*) ([^ ]*)", re.IGNORECASE)
    edges = {}
    for line in lines:
        edgeRegexResult = edgeRegex.search(line)
        if edgeRegexResult:
            source = edgeRegexResult.group(1)
            target = edgeRegexResult.group(2)
            if source not in edges:
                edges[source] = set()
            if target not in edges[source]:
                edges[source].add(target)

    chains = []
    for key, value in edges.iteritems():
        chains.append({"source": key, "targets": list(value)})

    out = {
        "type": "generic",
        "data": chains
    }
    print json.dumps(out, indent=4, separators=(',', ': '))
