import json
from timeit import default_timer as timer

class LazloBabaiGraph:
    def __init__(self, edges):
        self.edges = edges
        self.vertices = set()
        for edge in edges:
            self.vertices.update(edge)
        self.adjacency_list = {v: set() for v in self.vertices}
        for u, v in edges:
            self.adjacency_list[u].add(v)
            self.adjacency_list[v].add(u)

def initial_partitioning(graph):
    partitions = {}
    for v in graph.vertices:
        degree = len(graph.adjacency_list[v])
        if degree not in partitions:
            partitions[degree] = []
        partitions[degree].append(v)
    return partitions

def refine_partitions(graph, partitions, vertex):
    new_partitions = {}
    for part in partitions.values():
        for v in part:
            adjacency = len(graph.adjacency_list[v] & graph.adjacency_list[vertex])
            if adjacency not in new_partitions:
                new_partitions[adjacency] = []
            new_partitions[adjacency].append(v)
    return new_partitions

def is_canonical_form(partitions):
    # Simplified canonical form check: compare sorted lists of partitions
    partition_list = sorted([sorted(part) for part in partitions.values()])
    return partition_list

def select_vertices(partitions):
    for part in partitions.values():
        for v in part:
            yield v

def babai_graph_isomorphism(G1, G2):
    if len(G1.vertices) != len(G2.vertices) or len(G1.edges) != len(G2.edges):
        return False

    partitions1 = initial_partitioning(G1)
    partitions2 = initial_partitioning(G2)

    return isomorphism_helper(G1, partitions1, G2, partitions2)

def isomorphism_helper(G1, partitions1, G2, partitions2):
    if is_canonical_form(partitions1) == is_canonical_form(partitions2):
        return True

    for vertex in select_vertices(partitions1):
        new_partitions1 = refine_partitions(G1, partitions1, vertex)
        new_partitions2 = refine_partitions(G2, partitions2, vertex)

        if isomorphism_helper(G1, new_partitions1, G2, new_partitions2):
            return True

    return False

def load_lazlo_babai_graph(file_path):
    with open(file_path, 'r') as file:
        data = json.load(file)
    
    edges = [(edge['source'], edge['target']) for edge in data['edges']]
    return LazloBabaiGraph(edges)

if __name__ == "__main__":
    G1 = load_lazlo_babai_graph('resources/output/el_graph.json')
    G2 = load_lazlo_babai_graph('resources/output/graph.json')
        
    print("Running Lazlo-Babai algo...")
    
    start_time = timer()
    
    if len(G1.vertices) != len(G2.vertices) or len(G1.edges) != len(G2.edges):
        isomorphic = False
    else:
        partitions1 = initial_partitioning(G1)
        partitions2 = initial_partitioning(G2)

        isomorphic = isomorphism_helper(G1, partitions1, G2, partitions2)
    
    end_time = timer()
    elapsed_time = end_time - start_time
    
    if isomorphic:
        print("The graphs are isomorphic.")
    else:
        print("The graphs are not isomorphic.")
    
    print(f"Time taken: {elapsed_time:.9f} seconds")
