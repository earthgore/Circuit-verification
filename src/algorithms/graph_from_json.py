import json
import networkx as nx

def load_graph_from_json(file_path):
    with open(file_path, 'r') as file:
        data = json.load(file)
    
    G = nx.Graph()
    for node in data['nodes']:
        G.add_node(node['id'], label=node['label'])
    
    for edge in data['edges']:
        G.add_edge(edge['source'], edge['target'])
    
    return G