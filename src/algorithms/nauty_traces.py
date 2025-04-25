import json
from timeit import default_timer as timer

class Graph:
    def __init__(self, edges, labels=None):
        self.adj_list = {}
        self.labels = labels if labels else {}
        for u, v in edges:
            if u not in self.adj_list:
                self.adj_list[u] = []
            if v not in self.adj_list:
                self.adj_list[v] = []
            self.adj_list[u].append(v)
            self.adj_list[v].append(u)
        self.vertices = list(self.adj_list.keys())

    def degree(self, v):
        return len(self.adj_list[v])

def initial_partition(graph):
    partition = {}
    for v in graph.vertices:
        d = graph.degree(v)
        if d not in partition:
            partition[d] = []
        partition[d].append(v)
    return partition

def refine_partition(graph, partition):
    # Refine partitions based on neighbor partitions
    refined_partition = {}
    for part in partition.values():
        sub_partitions = {}
        for v in part:
            neighbor_degrees = tuple(sorted(graph.degree(n) for n in graph.adj_list[v]))
            if neighbor_degrees not in sub_partitions:
                sub_partitions[neighbor_degrees] = []
            sub_partitions[neighbor_degrees].append(v)
        for sub_part in sub_partitions.values():
            key = len(refined_partition)
            refined_partition[key] = sub_part
    return refined_partition

def canonical_form(graph, partition):
    # Compute canonical form based on refined partitions
    labels = {}
    for i, part in enumerate(partition.values()):
        for v in part:
            labels[v] = i
    return labels

def backtrack(graph1, graph2, partition1, partition2, mapping):
    if len(mapping) == len(graph1.vertices):
        return True, mapping

    for part1, part2 in zip(partition1.values(), partition2.values()):
        for v1 in part1:
            if v1 in mapping:
                continue
            for v2 in part2:
                if v2 in mapping.values():
                    continue
                mapping[v1] = v2
                success, result = backtrack(graph1, graph2, partition1, partition2, mapping)
                if success:
                    return True, result
                del mapping[v1]
            return False, None
    return False, None

def nauty_traces_isomorphism(graph1, graph2):
    if len(graph1.vertices) != len(graph2.vertices):
        return False

    partition1 = initial_partition(graph1)
    partition2 = initial_partition(graph2)

    refined_partition1 = refine_partition(graph1, partition1)
    refined_partition2 = refine_partition(graph2, partition2)

    canon_form1 = canonical_form(graph1, refined_partition1)
    canon_form2 = canonical_form(graph2, refined_partition2)

    return canon_form1 == canon_form2

def load_graph_from_json(file_path):
    with open(file_path, 'r') as file:
        data = json.load(file)
    
    edges = [(edge['source'], edge['target']) for edge in data['edges']]
    labels = {node['id']: node['label'] for node in data['nodes']}
    return Graph(edges, labels)

if __name__ == "__main__":
    G1 = load_graph_from_json('rand_graph_1000000.json')
    G2 = load_graph_from_json('rand_graph_1000000.json')
        
    print("Running Nauty-Traces algo...")
    
    start_time = timer()
    isomorphic = nauty_traces_isomorphism(G1, G2)
    end_time = timer()
    
    elapsed_time = end_time - start_time
    
    if isomorphic:
        print("The graphs are isomorphic.")
    else:
        print("The graphs are not isomorphic.")
    
    print(f"Time taken: {elapsed_time:.6f} seconds")
