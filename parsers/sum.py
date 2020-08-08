#!/usr/bin/env python2

# -*- coding: utf-8 -*-

# Example:
# python2 sum.py foo/calls.txt foo/methods.txt bar/methods.txt "fooPrefix" "barPrefix"

import json
import os.path
import sys

import utils.logging
import utils.serializer
import traversal.code
import traversal.generic

def parseMethods(methods):
    parsedMethods = None
    try:
        with open(methods) as f:
            parsedMethods = f.read()
    except IOError:
        logger.log("trace", "Treating passed methods as string: " + str(methods))
        parsedMethods = methods

    pattern = "|".join([x.strip() for x in parsedMethods.splitlines()]).strip("|")
    if len(pattern.strip()) == 0:
        pattern = ".*"

    return pattern

if __name__ == "__main__":
    logger = utils.logging.Logger(True)

    filenameCalls = None
    sourceMethods = None
    targetMethods = None
    sourcePrefix = ""
    targetPrefix = ""
    sourceName = ""
    targetName = ""
    is_graph_unpickled = False

    if sys.argv[1].startswith("-"):
        args = sys.argv[1:]
        while len(args):
            option = args[0]
            value = args[1]
            if option == "-c" or option == "--calls":
                filenameCalls = value
            elif option == "-m" or option == "--source-methods":
                sourceMethods = value
            elif option == "-M" or option == "--target-methods":
                targetMethods = value
            elif option == "-p" or option == "--source-prefix":
                sourcePrefix = value
            elif option == "-P" or option == "--target-prefix":
                targetPrefix = value
            elif option == "-n" or option == "--source-name":
                sourceName = value
            elif option == "-N" or option == "--target-name":
                targetName = value
            elif option == "--unpickle":
                is_graph_unpickled = bool(value)
            args = args[2:]
    else:
        filenameCalls = sys.argv[1]
        sourceMethods = sys.argv[2]
        targetMethods = sys.argv[3]
        if len(sys.argv) > 4:
            sourcePrefix = sys.argv[4]
        if len(sys.argv) > 5:
            targetPrefix = sys.argv[5]
        if len(sys.argv) > 6:
            sourceName = sys.argv[6]
        if len(sys.argv) > 7:
            targetName = sys.argv[7]

    with open(filenameCalls) as f:
        lines = json.loads(f.read())
    sourceMethods = parseMethods(sourceMethods)
    targetMethods = parseMethods(targetMethods)

    name = None
    if sourceName and targetName:
        name = "./data/" + sourceName + "_" + targetName

    serializer = utils.serializer.Serializer(name)
    traversers = [
        traversal.code.Code(logger, serializer),
        traversal.generic.Generic(logger, serializer)
    ]
    for traverser in traversers:
        if is_graph_unpickled:
            traverser = serializer.pickle2graph(traverser)
        traverser.traverse(lines, sourceMethods, targetMethods, sourcePrefix, targetPrefix)
