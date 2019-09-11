import collections
import os
import re

import networkx as nx

from .traverser import Traverser

class Code(Traverser):
    def __init__(self, logger, serializer):
        Traverser.__init__(self, logger, serializer, 'code')

    def find(self):
        print "# Calls"
        self.graphChains = nx.DiGraph()
        countCases = 1
        pathParents = {}
        for source in self.sources:
            self.logger.log("trace", "Finding chains from " + str(source))
            for target in self.targets:
                try:
                    path = nx.shortest_path(self.graph, source, target)
                    if len(path) < 1:
                        continue
                    joinedParents = "_".join(path[:-1])
                    if joinedParents in pathParents:
                        continue

                    caseBuffer = ""
                    self.graphChains.add_path([ x.split(".")[-1] for x in path ])
                    pathParents[joinedParents] = 1
                    for idx, node in enumerate(path):
                        # Already printed from extracted targets
                        if (idx == len(path) - 1):
                            continue

                        # Ommit packages
                        caseBuffer += node.split(".")[-1] + "\n"
                        if (idx == len(path) - 2):
                            orderedTargets = self.extractOrderedTargets(self.calls, node)
                            for orderedTargetName in orderedTargets:
                                caseBuffer += "    " + orderedTargetName + "\n"
                                if not orderedTargetName in self.countTotalTargets:
                                    self.countTotalTargets[orderedTargetName] = 0
                                self.countTotalTargets[orderedTargetName] += 1

                    print ""
                    print "### " + str(countCases)
                    print "```"
                    print caseBuffer.encode("utf-8").strip()
                    print "```"
                    countCases += 1
                except Exception, e:
                    self.logger.log("error", e.__class__.__name__ + ":" + unicode(e.message).encode('utf-8'))
                    continue

    def toMethodNameSimple(self, method):
        return re.sub("\(.*", "", method.split(self.delimiter)[1])

    # Manually add edges for methods which 
    # implement or override methods from other classes
    def addRelatedEdges(self, graph, sources, classesOfMethods):
        builtInMethodRegex = re.compile("(<init>\(|equals\(|toString\()")
        sourcesToCheck = list(self.sources)
        sourcesAlreadyChecked = set()
        while len(sourcesToCheck) > 0:
            sourcesQueue = sourcesToCheck[:]
            sourcesToCheck = []
            for source in sourcesQueue:
                self.logger.log("trace", "Adding subclass edges for " + str(source))
                try:
                    neighbors = self.graph.neighbors(source)
                    for n1 in neighbors:
                        c1 = n1.split(self.delimiter)[0]
                        m1 = n1.split(self.delimiter)[1]
                        if builtInMethodRegex.search(m1):
                            continue
                        if m1 in self.classesOfMethods:
                            for c in self.classesOfMethods[m1]:
                                if c == c1:
                                    continue
                                newTarget = c + self.delimiter + m1
                                if not newTarget in sourcesAlreadyChecked:
                                    sourcesAlreadyChecked.add(newTarget)
                                    sourcesToCheck.append(newTarget)
                                if n1 in self.serializedSources and newTarget in self.serializedTargets:
                                    continue
                                self.graph.add_edge(n1, newTarget)
                except Exception, e:
                    self.logger.log("error", e.__class__.__name__ + ":" + unicode(e.message).encode('utf-8'))
                    continue

    def extractOrderedTargets(self, calls, x):
        orderedTargets = []
        for y in calls[x]:
            orderedTargets.append(re.sub("\(.*", "", y.split(self.delimiter)[1]))
        return orderedTargets

    def addClassesOfMethods(self, callerName):
        callerClass = callerName.split(self.delimiter)[0]
        callerMethod = callerName.split(self.delimiter)[1]
        if not callerMethod in self.classesOfMethods or (self.classesOfMethods[callerMethod] is None):
            self.classesOfMethods[callerMethod] = set()
        self.classesOfMethods[callerMethod].add(callerClass)
