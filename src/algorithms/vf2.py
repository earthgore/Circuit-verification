from networkx.algorithms import isomorphism
from timeit import default_timer as timer


def subgraph_monomorphism(subgraph, graph):
    def node_match(node1, node2):
        return node1.get('label') == node2.get('label')
    
    def edge_match(edge1, edge2):
        return edge1.get('label') == edge2.get('label')
    
    start_time = timer()

    matcher = isomorphism.GraphMatcher(graph, subgraph, node_match=node_match, edge_match=edge_match)
    is_isomorphic = matcher.subgraph_is_monomorphic()
    
    mapping = matcher.mapping
    end_time = timer()
    elapsed_time = end_time - start_time

    return is_isomorphic, mapping, elapsed_time


def subgraph_isomorphism(subgraph, graph):
    def node_match(node1, node2):
        return node1.get('label') == node2.get('label')
    
    def edge_match(edge1, edge2):
        return edge1.get('label') == edge2.get('label')
    
    start_time = timer()

    matcher = isomorphism.GraphMatcher(graph, subgraph, node_match=node_match, edge_match=edge_match)
    is_isomorphic = matcher.subgraph_is_isomorphic()
    
    mapping = matcher.mapping
    end_time = timer()
    elapsed_time = end_time - start_time

    return is_isomorphic, mapping, elapsed_time


if __name__ == "__main__":
    from graph_from_json import load_graph_from_json
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