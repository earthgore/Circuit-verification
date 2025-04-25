import matplotlib.pyplot as plt
import networkx as nx
import json


with open('output/el_graph_and.json', 'r') as file:
    data = json.load(file)
    
        
graph = nx.Graph()
for node in data["nodes"]:
    graph.add_node(node["id"], label=node["label"])
for edge in data["edges"]:
    graph.add_edge(edge["source"], edge["target"])

""""nodes": [
        {
            "id": 0,
            "label": "TP1"
        },
        {
            "id": 1,
            "label": "TP2"
        },
        {
            "id": 2,
            "label": "TP3"
        },
        {
            "id": 3,
            "label": "TN4"
        },
        {
            "id": 4,
            "label": "TN5"
        },
        {
            "id": 5,
            "label": "TN6"
        },
        {
            "id": 6,
            "label": "p1"
        },
        {
            "id": 7,
            "label": "VCC"
        },
        {
            "id": 8,
            "label": "a"
        },
        {
            "id": 9,
            "label": "b"
        },
        {
            "id": 10,
            "label": "s"
        },
        {
            "id": 11,
            "label": "p2"
        },
        {
            "id": 12,
            "label": "GND"
        }
    ]"""
fig, ax = plt.subplots(figsize=(5.5, 5.5))
pos = {
    5: (20, 20), #TN6
    4: (5, 0), #TN5
    3: (5, 20), #TN4
    1: (0, 40), #TP2
    2: (20, 40), #TP1
    0: (10, 40), #TP3
    10: (25, 30), #S
    6: (5, 30), #P1
    7: (5, 50), #VCC
    12: (5, -10), #GND
    9: (-10, 30), #b
    8: (-5, 30), #a
    11: (5, 10) #p2
}

nx.draw(graph, pos, with_labels=True, labels=nx.get_node_attributes(graph, 'label'), ax=ax)
plt.show()