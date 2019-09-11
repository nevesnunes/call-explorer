import json
import os
import Queue

import networkx as nx

class Serializer:
    def __init__(self, name):
        if not name:
            name = 'unnamed'
        self.savedGraphName = name + '.gpickle'
        self.savedJsonName = name + '.json'
        
    def graph2json(self, graph, sources):
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

    def graph2pickle(self, graph, sources, reducedSources, targets):
        nx.write_gpickle(graph, self.savedGraphName)
        with open(self.savedJsonName, 'w') as outfile:
            outfile.write(json \
                    .dumps({"sources" : list(sources), "reducedSources": list(reducedSources), "targets":list(targets)}, separators=(',', ': ')))

    def pickle2graph(self, traverser):
        if not os.path.isfile(self.savedGraphName):
            return traverser

        traverser.graph = nx.read_gpickle(self.savedGraphName)

        if not os.path.isfile(self.savedJsonName):
            return traverser

        with open(self.savedJsonName) as f:
            try:
                lines = json.loads(f.read())
                traverser.serializedSources = set(lines["sources"])
                traverser.serializedReducedSources = set(lines["reducedSources"])
                traverser.serializedTargets = set(lines["targets"])
            except:
                pass

        return traverser
