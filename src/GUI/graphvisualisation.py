import matplotlib.pyplot as plt
import networkx as nx
import json


with open('resources/output/graph_inv.json', 'r') as file:
    data = json.load(file)
    
        
graph = nx.Graph()
for node in data["nodes"]:
    graph.add_node(node["id"], label=node["label"])
for edge in data["edges"]:
    graph.add_edge(edge["source"], edge["target"])


fig, ax = plt.subplots(figsize=(5.5, 5.5))
'''pos = {
    0: (0, 0),
    1: (10, 0),
    2: (20, 0),
    3: (10, 40),
    4: (20, 40),
    5: (0, 40),
    26: (0, 20),
    27: (15, 20),
    44: (5, 30),
    45: (5, 10),
    60: (10, 20),
    61: (20, 20),
    65: (15, 0),
}'''

nx.draw(graph, None, with_labels=True, labels=nx.get_node_attributes(graph, 'label'), ax=ax)
plt.show()