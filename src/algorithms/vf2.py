import json
import networkx as nx
from networkx.algorithms import isomorphism
from timeit import default_timer as timer

def load_graph_from_json(file_path):
    with open(file_path, 'r') as file:
        data = json.load(file)
    
    G = nx.Graph()
    for node in data['nodes']:
        G.add_node(node['id'], label=node['label'])
    
    for edge in data['edges']:
        G.add_edge(edge['source'], edge['target'])
    
    return G

if __name__ == "__main__":
    G1 = load_graph_from_json('resources/output/graph.json')
    G2 = load_graph_from_json('resources/output/el_graph.json')
    
    def node_match(node1, node2):
        return node1.get('label') == node2.get('label')
        
    print("Running VF2 algo...")
    
    start_time = timer()
    matcher = isomorphism.GraphMatcher(G1, G2, node_match=node_match)
    
    if matcher.is_isomorphic():
        print("The graphs are isomorphic.")
        print(matcher.mapping)
    else:
        print("The graphs are not isomorphic.")

    end_time = timer()
    elapsed_time = end_time - start_time

        
    print(f"Time taken: {elapsed_time:.6f} seconds")
