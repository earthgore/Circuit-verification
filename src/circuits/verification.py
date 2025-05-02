from src.algorithms.vf2 import subgraph_monomorphism
from src.circuits.ElectricalСircuit import ElecrticalCircuit
from src.circuits.TopologicalCircuit import TopologicalCircuit
from collections import defaultdict

def compress_parallel_nodes(nx_graph):
    G = nx_graph.copy()
    new_node_id = max(G.nodes) + 1
    grouped = defaultdict(list)

    # 1. Группируем подходящие вершины
    for node in G.nodes:
        if G.degree[node] != 3:
            continue
        label = G.nodes[node].get('label')
        if label not in ['N', 'P']:
            continue

        neighbors = list(G.neighbors(node))
        neighbors_set = frozenset(neighbors)

        # Получаем метки рёбер к каждому соседу
        edge_labels = tuple(
            sorted((n, G.get_edge_data(node, n).get('label')) for n in neighbors)
        )

        key = (label, neighbors_set, edge_labels)
        grouped[key].append(node)

    # 2. Сжимаем группы с ≥2 вершинами
    for (label, neighbors_set, _), nodes in grouped.items():
        if len(nodes) < 2:
            continue

        new_node = new_node_id
        new_node_id += 1
        G.add_node(new_node)
        G.nodes[new_node]['label'] = label

        # Добавляем рёбра к тем же соседям, с теми же метками
        for neighbor in neighbors_set:
            # Берём метку ребра от первой вершины
            edge_label = G.get_edge_data(nodes[0], neighbor).get('label')
            G.add_edge(new_node, neighbor)
            if edge_label is not None:
                G[new_node][neighbor]['label'] = edge_label

        # Удаляем старые вершины
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

        # Ищем только троечников с меткой N или P
        if degree != 3 or label not in ['N', 'P']:
            continue

        # Запускаем BFS с фильтром по метке и ребрам
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

            # Только 2/3 степень, троечники — с нужной меткой
            if current_degree == 3 and current_label != valid_label:
                continue
            if current_degree not in [2, 3]:
                continue

            local_visited.add(current)
            component.add(current)

            for neighbor in G.neighbors(current):
                edge_data = G.get_edge_data(current, neighbor, default={})
                neighbor_degree = G.degree[neighbor]

                # Если сосед — двойка и ребро gate, пропускаем
                if neighbor_degree == 2 and edge_data.get('label') == 'gate':
                    continue

                # Иначе, добавляем в очередь
                if neighbor not in local_visited:
                    queue.append(neighbor)

        # Считаем троечников
        deg3_nodes = [n for n in component if G.degree[n] == 3]
        if len(deg3_nodes) >= 2:
            components_to_merge.append((component, valid_label))
            visited.update(component)

    # Сжимаем компоненты
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

def verification(filename_electrical, name_electrical, filename_topological, name_topological):
    electrical_circuit = ElecrticalCircuit(name_electrical)
    electrical_circuit.load_NET(filename_electrical)
    electrical_circuit.compile()
    
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

    isomorph, mapping, time = subgraph_monomorphism(G2, G1)
    
    if isomorph:
        print("The graphs are isomorphic.")
    else:
        print("The graphs are not isomorphic.")

    print(mapping)
    topological_circuit.visualize_trans([])

    degrees = dict(electrical_circuit.nx_graph.degree())

    # Подсчитываем сколько вершин каждой степени
    degree_counts = {}

    for degree in degrees.values():
        if degree in degree_counts:
            degree_counts[degree] += 1
        else:
            degree_counts[degree] = 1

    # Выводим количество вершин каждой степени
    print("Количество вершин каждой степени связности:")
    for degree, count in sorted(degree_counts.items()):
        print(f"Степень {degree}: {count} вершины")

    degrees = dict(topological_circuit.nx_graph.degree())

    # Подсчитываем сколько вершин каждой степени
    degree_counts = {}

    for degree in degrees.values():
        if degree in degree_counts:
            degree_counts[degree] += 1
        else:
            degree_counts[degree] = 1

    # Выводим количество вершин каждой степени
    print("Количество вершин каждой степени связности:")
    for degree, count in sorted(degree_counts.items()):
        print(f"Степень {degree}: {count} вершины")
    
    print(f"Time taken: {time:.6f} seconds")


    

