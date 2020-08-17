#!/usr/bin/env python2

# -*- coding: utf-8 -*-

import json
import os
import re
import sys

if __name__ == "__main__":

    chains = []

    filename = sys.argv[1]
    with open(filename) as f:
        lines = f.readlines()
        lines = [x.strip() for x in lines] 

        nodeRegex = re.compile("^node ([^ ]*).*{(.*)}", re.IGNORECASE)
        edgeRegex = re.compile("^edge ([^ ]*) ([^ ]*)", re.IGNORECASE)
        nodes = {}
        edges = {}
        for line in lines:
            nodeRegexResult = nodeRegex.search(line)
            edgeRegexResult = edgeRegex.search(line)
            if nodeRegexResult:
                nodeKey = nodeRegexResult.group(1)
                nodeVal = nodeRegexResult.group(2)
                nodes[nodeKey] = nodeVal
            elif edgeRegexResult:
                source = edgeRegexResult.group(1)
                target = edgeRegexResult.group(2)
                if source not in nodes:
                    continue
                if nodes[source] not in edges:
                    edges[nodes[source]] = set()
                if source in nodes and target in nodes:
                    edges[nodes[source]].add(nodes[target])

        chains = []
        for key, value in edges.iteritems():
            chains.append({"source": key, "targets": list(value)})

        out = {
            "type": "generic",
            "data": chains
        }
        print json.dumps(out, indent=4, separators=(',', ': '))
