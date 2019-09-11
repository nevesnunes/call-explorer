import collections
import os
import re

import networkx as nx

from .traverser import Traverser

class Generic(Traverser):
    def __init__(self, logger, serializer):
        Traverser.__init__(self, logger, serializer, 'generic')

    def find(self):
        print "# Calls"
        self.graphChains = nx.DiGraph()
        countCases = 1
        seenPaths = {}

        oldSources = set()
        oldTargets = set()
        newSources = set(self.sources)
        newTargets = set(self.targets)
        while oldSources != newSources or oldTargets != newTargets:
            oldSources = set(newSources)
            oldTargets = set(newTargets)
            for source in oldSources:
                self.logger.log("trace", "Finding chains from " + str(source.encode('utf-8')))
                for target in oldTargets:
                    try:
                        path = nx.shortest_path(self.graph, source, target)
                        if len(path) < 1:
                            continue
                        joinedPath = "_".join(path)
                        if joinedPath in seenPaths:
                            continue

                        # Follow targets
                        if not target in newSources:
                            self.logger.log("trace", "Adding sub-dependencies for " + str(target.encode('utf-8')))
                            newSources.add(target)
                        try:
                            for n in self.graph.neighbors(target):
                                if n not in newTargets:
                                    newTargets.add(n)
                        except nx.NetworkXError:
                            continue

                        caseBuffer = ""
                        self.graphChains.add_path([ x.split(".")[-1] for x in path ])
                        seenPaths[joinedPath] = 1
                        for idx, node in enumerate(path):
                            # Already printed from extracted targets
                            if (idx == len(path) - 1):
                                continue

                            # Ommit packages
                            if (idx == len(path) - 2):
                                orderedTargets = self.extractOrderedTargets(self.calls, node)
                                joinedFullPath = source + "_".join(orderedTargets)
                                if joinedFullPath in seenPaths:
                                    continue
                                seenPaths[joinedFullPath] = 1

                                caseBuffer += node.split(".")[-1] + "\n"
                                for orderedTargetName in orderedTargets:
                                    caseBuffer += "    " + orderedTargetName + "\n"
                                    if not orderedTargetName in self.countTotalTargets:
                                        self.countTotalTargets[orderedTargetName] = 0
                                    self.countTotalTargets[orderedTargetName] += 1

                        if caseBuffer:
                            print ""
                            print "### " + str(countCases)
                            print "```"
                            print caseBuffer.encode("utf-8").strip()
                            print "```"
                            countCases += 1
                    except Exception, e:
                        self.logger.log("error", e.__class__.__name__ + ":" + unicode(e.message).encode('utf-8'))
                        continue
        self.sources = newSources
        self.targets = newTargets

    def isNotHandled(self, lines):
        return "type" in lines and lines["type"] != self.handledType
