# -*- coding: utf-8 -*-

# Example:
# python2 sum.py foo/calls.txt foo/methods.txt bar/methods.txt ""

import collections
import json
import Queue
import os
import re
import sys

import networkx as nx

globals = {}

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

def toMethodNameSimple(method):
    return re.sub("\(.*", "", method.split(":")[1])

def extractOrderedTargets(calls, x):
    orderedTargets = []
    for y in calls[x]:
        orderedTargets.append(re.sub("\(.*", "", y.split(":")[1]))
    return orderedTargets

def log(filename, message):
    if globals["LOG"]:
        globals[filename].write(message + "\n")

def graph2json(graph, sources):
    nodeq=Queue.Queue()
    ds = []
    for source in sources:
        traversed_nodes=[]
        cur_node=source.split(".")[-1]
        d = {"name" : cur_node, "children" : [] }
        cur_list = d["children"]
        nodeq.put((cur_node, cur_list))
        while not nodeq.empty():
            (cur_node, cur_list) = nodeq.get(block=True)
            if cur_node not in traversed_nodes:
                traversed_nodes.append(cur_node)
                try:
                    for n in graph.neighbors(cur_node):
                        if n not in traversed_nodes:
                            cur_list.append({"name" : n, "children" : []})
                            nodeq.put((n, cur_list[-1]["children"]), block=True)
                except nx.NetworkXError:
                    continue
        ds.append(d)

    with open('chains.json', 'w') as outfile:
        outfile.write(json \
            .dumps(ds, indent=4, separators=(',', ': ')) \
            .replace('"children": []', '"size": 1'))

if __name__ == "__main__":
    globals["LOG"] = True
    for logname in [ "error", "trace"]:
        try:
            os.remove("./" + logname + ".txt")
        except OSError:
            pass
        globals[logname] = open("./" + logname + ".txt", "a")

    filenameCalls = sys.argv[1]
    with open(filenameCalls) as f:
        lines = f.readlines()
    lines = [x.strip() for x in lines] 

    filenameSourceMethods = sys.argv[2]
    with open(filenameSourceMethods) as f:
        sourceMethods = f.readlines()
    sourceMethods = "|".join([x.strip() for x in sourceMethods])

    filenameTargetMethods = sys.argv[3]
    with open(filenameTargetMethods) as f:
        targetMethods = f.readlines()
    targetMethods = "|".join([x.strip() for x in targetMethods])

    sourcePrefix = ""
    if len(sys.argv) > 4:
        sourcePrefix = sys.argv[4]

    targetPrefix = ""
    if len(sys.argv) > 5:
        targetPrefix = sys.argv[5]

    calls = {}
    classesOfMethods = {}
    graph = nx.DiGraph()
    sources = set()
    targets = set()
    targetCodeSnippets = {}

    # 2 ways of finding chains: By source class or by source method
    methodRegex = re.compile("^M:.*")
    sourcePrefixedRegex = ""
    if sourcePrefix:
        sourcePrefixedRegex = re.compile(sourcePrefix + ".*:(.*)\(.*\) .*", re.IGNORECASE)
    sourceRegex = re.compile(":(" + sourceMethods + ")\(.*\) .*", re.IGNORECASE)
    targetRegex = re.compile(" \(.\).*" + targetPrefix + ".*:(" + targetMethods + ")\(.*\)(| .*)", re.IGNORECASE)
    targetCodeSnippetRegex = re.compile(targetPrefix + ".*:(" + targetMethods + ").* \(.*\)", re.IGNORECASE)
    for idx, line in enumerate(lines):
        if methodRegex.search(line):
            callerName = extractCall(line.split(" ")[0][2:])

            callerClass = callerName.split(":")[0]
            callerMethod = callerName.split(":")[1]
            if not callerMethod in classesOfMethods or (classesOfMethods[callerMethod] is None):
                classesOfMethods[callerMethod] = set()
            classesOfMethods[callerMethod].add(callerClass)

            calledName = extractCall(line.split(" ")[1][3:])

            if sourceRegex.search(line) or (sourcePrefix and sourcePrefixedRegex.search(line)):
                sources.add(callerName)
            if targetRegex.search(line):
                targets.add(calledName)

                # Remember order of called targets
                if not callerName in calls or (calls[callerName] is None):
                    calls[callerName] = collections.OrderedDict()
                if not calledName in calls[callerName] or (calls[callerName][calledName] is None):
                    calls[callerName][calledName] = 1

                # Remember order of snippets
                if targetCodeSnippetRegex.search(line):
                    sourceSnippets = line.split(" (Source)")
                    if len(sourceSnippets) > 1:
                        snippet = sourceSnippets[1]
                        calledNameSimple = toMethodNameSimple(calledName)
                        if not calledNameSimple in targetCodeSnippets or (targetCodeSnippets[calledNameSimple] is None):
                            targetCodeSnippets[calledNameSimple] = collections.OrderedDict()
                        if not snippet in targetCodeSnippets[calledNameSimple] or (targetCodeSnippets[calledNameSimple][snippet] is None):
                            targetCodeSnippets[calledNameSimple][snippet] = 1

            # Avoid self loops
            if not callerName == calledName:
                graph.add_edge(callerName, calledName)

    # Manually add edges for methods which 
    # implement or override methods from other classes
    builtInMethodRegex = re.compile("(<init>\(|equals\(|toString\()")
    sourcesToCheck = list(sources)
    sourcesAlreadyChecked = set()
    while len(sourcesToCheck) > 0:
        sourcesQueue = sourcesToCheck[:]
        sourcesToCheck = []
        for source in sourcesQueue:
            log("trace", "Adding subclass edges for " + str(source))
            try:
                neighbors = graph.neighbors(source)
                for n1 in neighbors:
                    c1 = n1.split(":")[0]
                    m1 = n1.split(":")[1]
                    if builtInMethodRegex.search(m1):
                        continue
                    if m1 in classesOfMethods:
                        for c in classesOfMethods[m1]:
                            if c == c1:
                                continue
                            newTarget = c + ":" + m1
                            graph.add_edge(n1, newTarget)
                            if not newTarget in sourcesAlreadyChecked:
                                sourcesAlreadyChecked.add(newTarget)
                                sourcesToCheck.append(newTarget)
            except Exception, e:
                log("error", e.__class__.__name__ + ":" + str(e))
                continue

    # Remove sources which are pointed to by parent sources.
    # This reduces method call chains to the longest paths.
    reducedSources = set(sources)
    sources2 = set(sources)
    for source1 in sources:
        log("trace", "Reducing chains from " + str(source1))
        for source2 in sources2:
            if source1 == source2:
                continue
            try:
                nx.shortest_path(graph, source1, source2)
                reducedSources.remove(source2)
            except:
                continue
    sources = reducedSources

    # Find method call chains
    print "# Calls"
    countCases = 1
    countTotalTargets = {}
    graphChains = nx.DiGraph()
    pathParents = {}
    for source in sources:
        log("trace", "Finding chains from " + str(source))
        for target in targets:
            try:
                path = nx.shortest_path(graph, source, target)
                if len(path) < 1:
                    continue
                joinedParents = "_".join(path[:-1])
                if joinedParents in pathParents:
                    continue

                caseBuffer = ""
                graphChains.add_path([ x.split(".")[-1] for x in path ])
                pathParents[joinedParents] = 1
                for idx, node in enumerate(path):
                    # Already printed from extracted targets
                    if (idx == len(path) - 1):
                        continue

                    # Ommit packages
                    caseBuffer += node.split(".")[-1] + "\n"
                    if (idx == len(path) - 2):
                        orderedTargets = extractOrderedTargets(calls, node)
                        for orderedTargetName in orderedTargets:
                            caseBuffer += "    " + orderedTargetName + "\n"
                            if not orderedTargetName in countTotalTargets:
                                countTotalTargets[orderedTargetName] = 0
                            countTotalTargets[orderedTargetName] += 1

                print ""
                print "### " + str(countCases)
                print "```"
                print caseBuffer.encode("utf-8").strip()
                print "```"
                countCases += 1
            except Exception, e:
                log("error", e.__class__.__name__ + ":" + str(e))
                continue

    # Summarize the total number of target calls
    print ""
    print "# Total"
    print "```"
    for key, value in sorted(countTotalTargets.iteritems(), key=lambda (k,v): (v,k)):
        print key + ":" + str(value)
        if key in targetCodeSnippets:
            for snippet in targetCodeSnippets[key]:
                print "    " + snippet.encode("utf-8").strip()
    print "```"

    # Print graph
    graph2json(graphChains, sources)

    # Cleanup
    globals["error"].close()
    globals["trace"].close()
