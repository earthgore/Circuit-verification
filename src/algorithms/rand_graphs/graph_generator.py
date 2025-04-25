import json
import random

def generate_random_graph(num_nodes):
    nodes = [{"id": i + 1, "label": chr(65 + i)} for i in range(num_nodes)]
    
    edges = set()
    for i in range(num_nodes):
        while True:
            target = random.randint(1, num_nodes)
            if target != i + 1:
                edges.add((min(i + 1, target), max(i + 1, target)))
                break

    for _ in range(random.randint(0, num_nodes)):
        source = random.randint(1, num_nodes)
        target = random.randint(1, num_nodes)
        if source != target:
            edges.add((min(source, target), max(source, target)))

    edges = [{"source": source, "target": target} for source, target in edges]

    graph = {
        "nodes": nodes,
        "edges": edges
    }

    return graph

def save_graph_to_json(graph, filename):
    with open(filename, 'w') as file:
        json.dump(graph, file, indent=4)

num_nodes = 10000000
graph = generate_random_graph(num_nodes)
filename = f"rand_graph_{num_nodes}.json"
save_graph_to_json(graph, filename)
print(f"Graph saved to {filename}")
