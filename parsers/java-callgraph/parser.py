#!/usr/bin/env python2

# -*- coding: utf-8 -*-

import json
import os
import re
import sys

def extractArgs(methodName):
    args = re.search("\(.*?\)", methodName).group()
    args = args.replace("(", "")
    args = args.replace(")", "")
    args = args.split(",")
    argNames = []
    for arg in args:
        argNames.append(arg.split(".")[-1])
    return argNames

def extractCall(method):
    className = method.split(":")[0]
    methodName = method.split(":")[1]
    methodNameSimple = re.sub("\(.*$", "", methodName)
    return className + \
	":" + \
	methodNameSimple + \
	"(" + \
	", ".join(extractArgs(methodName)) + \
	")"

def normalizedEncoding(text):
    try:
        return text.decode("utf-8")
    except UnicodeDecodeError:
        return text.decode("latin-1")

if __name__ == "__main__":

    chains = []

    filenames_list = sys.argv[1]
    with open(filenames_list) as f:
        filenames = f.readlines()
    filenames = [x \
            .strip() \
            .decode("string-escape") \
            .decode("utf-8") \
            for x in filenames] 

    for filename in filenames:
        names = filename.split('/')
        basename = names[len(names) - 2]

        with open(filename) as f:
            lines = f.readlines()
        lines = [x.strip() for x in lines] 

        delimiter = ' '
        ignoreRegex = re.compile("^#\|^[ \t]*$", re.IGNORECASE)
        builtInMethodRegex = re.compile("(<init>\(|equals\(|toString\()")
        tokenRegex = re.compile("^M:.*")
        tokens = {}
        for line in lines:
            results = {}
            if ignoreRegex.search(line) or builtInMethodRegex.search(line):
                continue
            if tokenRegex.search(line):
                callerName = extractCall(line.split(delimiter)[0][2:])
                calledName = extractCall(line.split(delimiter)[1][3:])
                results["source"] = callerName
                results["targets"] = [calledName]
                sourceSnippets = line.split(" (Source)")
                if len(sourceSnippets) > 1:
                    results["snippet"] = normalizedEncoding(sourceSnippets[1])
                chains.append(results)

    out = {
        "type": "code",
        "methodDelimiter": ":",
        "data": chains
    }
    print json.dumps(out, indent=4, separators=(',', ': '))
