import matplotlib.pyplot as plt
import networkx as nx
import json


with open('resources/output/graph.json', 'r') as file:
    data = json.load(file)
    
        
graph = nx.Graph()
for node in data["nodes"]:
    graph.add_node(node["id"], label=node["label"])
for edge in data["edges"]:
    graph.add_edge(edge["source"], edge["target"])


# Считаем степени вершин
degrees = dict(graph.degree())

# Создаем позиции для рисования
pos = {}
x_spacing = 1.5  # Расстояние между вершинами по X
sorted_nodes = sorted(degrees.items(), key=lambda x: (-x[1], x[0]))  # Сортируем: сначала по степени, потом по ID

for i, (node, degree) in enumerate(sorted_nodes):
    x = i * x_spacing
    y = degree  # Y равен степени вершины
    pos[node] = (x, y)

# Рисуем граф
plt.figure(figsize=(20, 10))
nx.draw(
    graph,
    pos,
    with_labels=True,
    node_size=600,
    node_color='lightgreen',
    edge_color='gray',
    font_size=10
)

# Подписываем степени отдельно
for node, (x, y) in pos.items():
    plt.text(x, y + 0.5, f"deg={degrees[node]}", ha='center', fontsize=8, color='red')

plt.title("Твой граф: вершины подняты по степени связности", fontsize=18)
plt.axis('off')
plt.show()