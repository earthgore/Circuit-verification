from src.algorithms.vf2 import subgraph_monomorphism
from src.algorithms.vf2 import subgraph_isomorphism
from src.circuits.ElectricalСircuit import ElecrticalCircuit
from src.circuits.TopologicalCircuit import TopologicalCircuit
from collections import defaultdict
from timeit import default_timer as timer

def compress_parallel_nodes(nx_graph):
    G = nx_graph.copy()
    new_node_id = max(G.nodes) + 1
    grouped = defaultdict(list)

    for node in G.nodes:
        if G.degree[node] != 3:
            continue
        label = G.nodes[node].get('label')
        if label not in ['N', 'P']:
            continue

        neighbors = list(G.neighbors(node))
        neighbors_set = frozenset(neighbors)

        edge_labels = tuple(
            sorted((n, G.get_edge_data(node, n).get('label')) for n in neighbors)
        )

        key = (label, neighbors_set, edge_labels)
        grouped[key].append(node)

    for (label, neighbors_set, _), nodes in grouped.items():
        if len(nodes) < 2:
            continue

        new_node = new_node_id
        new_node_id += 1
        G.add_node(new_node)
        G.nodes[new_node]['label'] = label

        for neighbor in neighbors_set:
            edge_label = G.get_edge_data(nodes[0], neighbor).get('label')
            G.add_edge(new_node, neighbor)
            if edge_label is not None:
                G[new_node][neighbor]['label'] = edge_label

        for n in nodes:
            G.remove_node(n)

    return G

def compress_series_nodes(nx_graph):
    G = nx_graph.copy()
    visited = set()
    new_node_id = max(G.nodes) + 1
    components_to_merge = []

    for node in G.nodes:
        if node in visited:
            continue

        degree = G.degree[node]
        label = G.nodes[node].get('label')

        if degree != 3 or label not in ['N', 'P']:
            continue

        queue = [node]
        component = set()
        local_visited = set()
        valid_label = label

        while queue:
            current = queue.pop()
            if current in local_visited:
                continue

            current_degree = G.degree[current]
            current_label = G.nodes[current].get('label')

            if current_degree == 3 and current_label != valid_label:
                continue
            if current_degree not in [2, 3]:
                continue

            local_visited.add(current)
            component.add(current)

            for neighbor in G.neighbors(current):
                edge_data = G.get_edge_data(current, neighbor, default={})
                neighbor_degree = G.degree[neighbor]

                if neighbor_degree == 2 and edge_data.get('label') == 'gate':
                    continue

                if neighbor not in local_visited:
                    queue.append(neighbor)

        deg3_nodes = [n for n in component if G.degree[n] == 3]
        if len(deg3_nodes) >= 2:
            components_to_merge.append((component, valid_label))
            visited.update(component)

    for comp, label in components_to_merge:
        new_node = new_node_id
        new_node_id += 1

        G.add_node(new_node)
        G.nodes[new_node]['label'] = label

        external_neighbors = set()
        for n in comp:
            for nb in G.neighbors(n):
                if nb not in comp:
                    external_neighbors.add(nb)

        for nb in external_neighbors:
            G.add_edge(new_node, nb)

        for n in comp:
            G.remove_node(n)

    return G

def verification(filename_electrical, name_electrical=None, filename_topological=None, name_topological=None, topological_circuit=None):
    start_time = timer()
    electrical_circuit = ElecrticalCircuit(name_electrical)
    electrical_circuit.load_NET(filename_electrical)
    electrical_circuit.compile()
    
    if topological_circuit == None:
        topological_circuit = TopologicalCircuit(name_topological)
        topological_circuit.load_CIF(filename_topological)
        topological_circuit.compile()

    print(f"electrical circuit : {electrical_circuit.nx_graph.number_of_nodes()} : {electrical_circuit.nx_graph.number_of_edges()}")
    print(f"topological circuit : {topological_circuit.nx_graph.number_of_nodes()} : {topological_circuit.nx_graph.number_of_edges()}")
    G1 = compress_series_nodes(electrical_circuit.nx_graph) 
    G1 = compress_parallel_nodes(G1)
    G2 = compress_series_nodes(topological_circuit.nx_graph)
    G2 = compress_parallel_nodes(G2)

    print(f"electrical circuit : {G1.number_of_nodes()} : {G1.number_of_edges()}")
    print(f"topological circuit : {G2.number_of_nodes()} : {G2.number_of_edges()}")

    isomorph, _ = subgraph_isomorphism(G2, G1)
    
    if isomorph:
        print("The graphs are isomorphic.")
        end_time = timer()
        elapsed_time = end_time - start_time
        return True, [], elapsed_time
    else:
        print("The graphs are not isomorphic.")
        lost_connection = search_lost_connections(electrical_circuit.nx_graph, topological_circuit.nx_graph)
        end_time = timer()
        elapsed_time = end_time - start_time
        return False, lost_connection, elapsed_time
        
def search_lost_connections(el_graph, top_graph):
    electrical_graph = el_graph.copy()
    topological_graph = top_graph.copy()
    el_degrees = dict(electrical_graph.degree())

    # Подсчитываем сколько вершин каждой степени
    el_degree_counts = {}

    for degree in el_degrees.values():
        if degree in el_degree_counts:
            el_degree_counts[degree] += 1
        else:
            el_degree_counts[degree] = 1

    top_degrees = dict(topological_graph.degree())

    # Подсчитываем сколько вершин каждой степени
    top_degree_counts = {}

    for degree in top_degrees.values():
        if degree in top_degree_counts:
            top_degree_counts[degree] += 1
        else:
            top_degree_counts[degree] = 1

    diff_degrees = {}
    sum_el = sum_top = 0
    for degree in set(el_degree_counts) | set(top_degree_counts):
        el_count = el_degree_counts.get(degree, 0)
        top_count = top_degree_counts.get(degree, 0)
        if el_count != top_count:
            print(f"Степень {degree}: {el_count} вершины и {top_count} вершины")
            sum_el += el_count
            sum_top += top_count
            diff_degrees[degree] = el_count - top_count

    
    if sum(k * v for k, v in diff_degrees.items()) != 0:
        return []
    
    for node, degree in top_degrees.items():
        if degree in diff_degrees:
            topological_graph.nodes[node]["label"] = "potential"
    
    for node, degree in el_degrees.items():
        if degree in diff_degrees:
            electrical_graph.nodes[node]["label"] = "potential"

    positive_diff_degrees = {k for k, v in diff_degrees.items() if v > 0}
    removable_el_nodes = [
        n for n, d in electrical_graph.nodes(data=True)
        if d.get("label") == "potential" and electrical_graph.degree[n] in positive_diff_degrees
    ]
    negative_diff_degrees = {k for k, v in diff_degrees.items() if v < 0}
    removable_top_nodes = [
        n for n, d in topological_graph.nodes(data=True)
        if d.get("label") == "potential" and topological_graph.degree[n] in negative_diff_degrees
    ]
    if(len(removable_el_nodes) <= len(removable_top_nodes)):
        for node_to_remove in removable_el_nodes:
            G_copy = electrical_graph.copy()
            G_copy.remove_node(node_to_remove)
            print(f"Удаляем из электрического: {node_to_remove}")

            isomorphic, mapping = subgraph_isomorphism(G_copy, topological_graph)
            if isomorphic:
                print(f"Удалена лишняя вершина электрического: {node_to_remove}")
                lost_connection = [n for n in topological_graph.nodes() if n not in mapping.keys()]
                return lost_connection
    else:
        for node_to_remove in removable_top_nodes:
            G_copy = topological_graph.copy()
            G_copy.remove_node(node_to_remove)
            print(f"Удаляем из топологического: {node_to_remove}")

            monomorphic, mapping = subgraph_monomorphism(electrical_graph, G_copy)
            if monomorphic:
                print(f"Удалена лишняя вершина топологического: {node_to_remove}")
                lost_connection = [n for n in topological_graph.nodes() if n not in mapping.values()]
                return lost_connection
            
    return []



def search_subcircuit(filename_electrical, name_electrical=None, filename_topological=None, name_topological=None, topological_circuit=None):
    start_time = timer()
    electrical_circuit = ElecrticalCircuit(name_electrical)
    electrical_circuit.load_NET(filename_electrical)
    electrical_circuit.compile()
    
    if topological_circuit == None:
        topological_circuit = TopologicalCircuit(name_topological)
        topological_circuit.load_CIF(filename_topological)
        topological_circuit.compile()

    G_copy = topological_circuit.nx_graph.copy()
    subcircuits = []
    isomorph, mapping = subgraph_isomorphism(electrical_circuit.nx_graph, G_copy)
    while isomorph:
        subcircuits.append(mapping.keys())
        for u, v in electrical_circuit.nx_graph.edges():
            mapped_u = None
            mapped_v = None

            for copy_node, subgraph_node in mapping.items():
                if subgraph_node == u:
                    mapped_u = copy_node
                elif subgraph_node == v:
                    mapped_v = copy_node

            if mapped_u is not None and mapped_v is not None and G_copy.has_edge(mapped_u, mapped_v):
                G_copy.remove_edge(mapped_u, mapped_v)
                
        isomorph, mapping = subgraph_isomorphism(electrical_circuit.nx_graph, G_copy)
    else:
        print("The subcircuit is not found.")
        end_time = timer()
        elapsed_time = end_time - start_time
        return subcircuits, elapsed_time
    

    