import json
import networkx as nx
from timeit import default_timer as timer

def weisfeiler_lehman_hash(graph, iterations=3):
    node_labels = {node: str(data.get('label', '')) for node, data in graph.nodes(data=True)}
    
    for i in range(iterations):
        new_labels = {}
        for node in graph.nodes():
            neighbor_labels = sorted(node_labels[neighbor] for neighbor in graph.neighbors(node))
            new_labels[node] = node_labels[node] + ''.join(neighbor_labels)
        node_labels = new_labels
    
    # Create a multiset label for the whole graph
    multiset_label = ''.join(sorted(node_labels.values()))
    return multiset_label

def load_graph_from_json(file_path):
    with open(file_path, 'r') as file:
        data = json.load(file)
    
    G = nx.Graph()
    for node in data['nodes']:
        G.add_node(node['id'], label=node['label'])
    
    for edge in data['edges']:
        G.add_edge(edge['source'], edge['target'])
    
    return G

def weisfeiler_lehman_isomorphism(G1, G2, iterations=3):
    G1_hash = weisfeiler_lehman_hash(G1, iterations)
    G2_hash = weisfeiler_lehman_hash(G2, iterations)
    return G1_hash == G2_hash

if __name__ == "__main__":
    G1 = load_graph_from_json('rand_graph_1000000.json')
    G2 = load_graph_from_json('rand_graph_1000000.json')
        
    print("Running Weisfeiler-Lehman algo...")
    
    start_time = timer()
    isomorphic = weisfeiler_lehman_isomorphism(G1, G2)
    end_time = timer()
    
    elapsed_time = end_time - start_time
    
    if isomorphic:
        print("The graphs are isomorphic.")
    else:
        print("The graphs are not isomorphic.")
    
    print(f"Time taken: {elapsed_time:.6f} seconds")
