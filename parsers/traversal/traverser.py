import collections
import json
import Queue
import os
import re

import networkx as nx

class Traverser:
    def __init__(self, logger, serializer, handledType):
        self.logger = logger
        self.serializer = serializer

        self.delimiter = ":"
        self.handledType = handledType

        self.calls = {}
        self.classesOfMethods = {}
        self.graph = nx.DiGraph()
        self.sources = set()
        self.targets = set()
        self.targetCodeSnippets = {}
        self.countTotalTargets = {}
        self.graphChains = nx.DiGraph()

        self.serializedSources = set()
        self.serializedReducedSources = set()
        self.serializedTargets = set()

    def traverse(self, lines, sourceMethods, targetMethods, sourcePrefix, targetPrefix):
        if self.isNotHandled(lines):
            return

        if "delimiter" in lines:
            self.delimiter = lines["delimiter"]

        self.addEdges(lines, sourceMethods, targetMethods, sourcePrefix, targetPrefix)
        self.addRelatedEdges(self.graph, self.sources, self.classesOfMethods)
        self.reduceSources()

        self.find()
        self.printSummary(self.countTotalTargets, self.targetCodeSnippets)
        self.serializer.graph2json(self.graphChains, self.sources)
        self.serializer.graph2pickle(self.graph, self.serializedSources, self.serializedReducedSources, self.serializedTargets)

    def find(self):
        raise NotImplementedError

    def extractOrderedTargets(self, calls, x):
        orderedTargets = []
        for y in calls[x]:
            orderedTargets.append(y)
        return orderedTargets

    def toMethodNameSimple(self, method):
        return method

    def addRelatedEdges(self, graph, sources, classesOfMethods):
        pass

    def addClassesOfMethods(self, callerName):
        pass

    def addSnippets(self, targetSnippets, line, calledName):
        if not "snippet" in line:
            return targetSnippets

        sourceSnippets = line["snippet"]
        if len(sourceSnippets) == 0:
            return targetSnippets

        snippet = "\n".join(sourceSnippets)
        calledNameSimple = self.toMethodNameSimple(calledName)
        if not calledNameSimple in targetSnippets or (targetSnippets[calledNameSimple] is None):
            targetSnippets[calledNameSimple] = collections.OrderedDict()
        if not snippet in targetSnippets[calledNameSimple] or (targetSnippets[calledNameSimple][snippet] is None):
            targetSnippets[calledNameSimple][snippet] = 1

        return targetSnippets

    def printSummary(self, countTotalTargets, targetCodeSnippets):
        print ""
        print "# Total"
        print "```"
        for key, value in sorted(countTotalTargets.iteritems(), key=lambda (k,v): (v,k)):
            print key + ":" + str(value)
            if key in targetCodeSnippets:
                for snippet in targetCodeSnippets[key]:
                    print "    " + re.sub('[\r\n]', '', snippet).encode("utf-8").strip()
        print "```"

    def addEdges(self, lines, sourceMethods, targetMethods, sourcePrefix, targetPrefix):
        # 2 ways of finding chains: By source class or by source method
        sourcePrefixedRegex = ""
        if sourcePrefix:
            sourcePrefixedRegex = re.compile(sourcePrefix + ".*", re.IGNORECASE)
        sourceRegex = re.compile(sourcePrefix + ".*(" + sourceMethods + ").*", re.IGNORECASE)
        targetRegex = re.compile(targetPrefix + ".*(" + targetMethods + ").*", re.IGNORECASE)
        for idx, line in enumerate(lines["data"]):
            callerName = line["source"]
            self.addClassesOfMethods(callerName)
            isCallerNameSerialized = callerName in self.serializedSources
            isCallerNameAdded = False
            for calledName in line["targets"]:    
                if sourceRegex.search(callerName) or (sourcePrefix and sourcePrefixedRegex.search(callerName)):
                    self.sources.add(callerName)
                if targetRegex.search(calledName):
                    self.targets.add(calledName)

                    # Remember order of called targets
                    if not callerName in self.calls or (self.calls[callerName] is None):
                        self.calls[callerName] = collections.OrderedDict()
                    if not calledName in self.calls[callerName] or (self.calls[callerName][calledName] is None):
                        self.calls[callerName][calledName] = 1

                    # Remember order of snippets
                    self.targetCodeSnippets = self.addSnippets(self.targetCodeSnippets, line, calledName)

                # Avoid self loops
                if not callerName == calledName:
                    # Avoid already added edges in serialized graph
                    if callerName in self.serializedSources and calledName in self.serializedTargets:
                        continue
                    self.graph.add_edge(callerName, calledName)
                    self.serializedSources.add(callerName)
                    self.serializedTargets.add(calledName)

    def reduceSources(self):
        # Remove sources which are pointed to by parent sources.
        # This reduces method call chains to the longest paths.
        reducedSources = set(self.sources)
        sources2 = set(self.sources)
        for source1 in self.sources:
            self.logger.log("trace", "Reducing chains from " + str(source1.encode('utf-8')))
            for source2 in sources2:
                if source2 in self.serializedReducedSources:
		    reducedSources.discard(source2)
                    continue
                if source1 == source2:
                    continue
                try:
                    nx.shortest_path(self.graph, source1, source2)
                    reducedSources.discard(source2)
                    self.serializedReducedSources.add(source2)
                except:
                    continue

        self.sources = reducedSources

    def isNotHandled(self, lines):
        return not "type" in lines or lines["type"] != self.handledType
