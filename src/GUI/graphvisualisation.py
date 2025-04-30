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


# Рисуем граф
plt.figure(figsize=(8, 5))
nx.draw(
    graph,
    None,
    with_labels=True,
    node_size=600,
    node_color='lightgreen',
    edge_color='gray',
    font_size=10
)


plt.title("Твой граф: ", fontsize=18)
plt.axis('off')
plt.show()