import re
import numpy as np
import pyvista as pv
import customtkinter as ctk
from itertools import combinations
import networkx as nx

def create_striped_texture(color1, color2, size=256, stripe_width=16):
    img = np.zeros((size, size, 3), dtype=np.uint8)
    for i in range(size):
        if (i // stripe_width) % 2 == 0:
            img[i, :, :] = color1
        else:
            img[i, :, :] = color2
    return pv.numpy_to_texture(img)

def parse_cif_to_graph(filename):
    """Parses a CIF file and creates a graph representation of nodes and edges with layer information."""
    graph = nx.Graph()
    current_layer = None
    node_id = 0

    with open(filename, 'r') as file:
        for line in file:
            line = line.strip()
            if line.startswith('L '):
                current_layer = line.split()[1].replace(';', '')
            elif line.startswith('P '):
                points = tuple(map(int, re.findall(r'-?\d+', line)))
                if len(points) >= 2 and len(set(points)) > 1:
                    graph.add_node(node_id, layer=current_layer, points=points)
                    node_id += 1
            elif line.startswith('4N '):
                parts = line.split()
                layer = re.sub(r'\d+', '', parts[1])
                points = tuple(map(int, [part.replace(';', '') for part in parts[2:]]))
                graph.add_node(node_id, layer=layer, points=points)
                node_id += 1

    return graph

def create_3d_plot(graph, selected_layers, show_labels, opacity=1.0):
    """Generates a 3D plot of the graph with selected layers, ensuring no gaps and grouping specific layers at the same level."""
    plotter = pv.Plotter(notebook=False)
    plotter.enable_anti_aliasing()

    layer_order = ['KN', 'P', 'NA', 'SP', 'SN', 'SI', 'CPE', 'CNE', 'CSI', 'CNA', 'CPA', 
                   'M1', 'CM1', 'M2', 'CM2', 'C', 'E', 'S', 'TN', 'TP', 'X', 'Y', 'ZERO']
    
    layer_thickness = 50
    space_beteween_layer = 20
    spike_width = 20
    spike_thickness = 200

    available_layers = [layer for layer in layer_order if layer in selected_layers]
    if not available_layers:
        plotter.add_text("No layers selected", position='upper_edge', font_size=14)
        plotter.show()
        return

    layer_groups = {
        'group1': ['P', 'NA'],
        'group2': ['CNA', 'CPA'], 
        'group3': ['CPE', 'CNE'],
        'group4': ['SP', 'SN', 'SI'],
        'group5': ['C', 'E', 'S', 'TN', 'TP', 'X', 'Y', 'ZERO']
    }

    layer_to_group = {}
    for group_name, layers in layer_groups.items():
        for layer in layers:
            layer_to_group[layer] = group_name

    
    layer_z_coordinates = {}
    assigned_groups = {}
    current_level = 0
    for layer in available_layers:
        if layer in layer_to_group:
            group = layer_to_group[layer]
            if group not in assigned_groups:
                for l in available_layers:
                    if l in layer_to_group and layer_to_group[l] == group:
                        layer_z_coordinates[l] = current_level
                assigned_groups[group] = current_level
                current_level += space_beteween_layer
        else:
            if layer not in layer_z_coordinates:
                layer_z_coordinates[layer] = current_level
                current_level += space_beteween_layer

    layer_colors = {
        'KN': [200, 0, 0], 'CM1': 'black', 'CM2': 'cyan', 'CSI': 'orange', 'P': 'blue',
        'NA': 'red', 'CPA': 'yellow', 'CNA': 'pink', 'CPE': 'brown', 'CNE': 'lightgreen',
        'SP': 'grey', 'SN': 'grey', 'SI': 'green', 'M1': 'magenta', 'M2': 'cyan',
        'C': 'violet', 'E': 'teal', 'S': 'olive', 'TN': 'maroon', 'TP': 'navy',
        'X': 'turquoise', 'Y': 'lime', 'ZERO': 'indigo'
    }

    max_size_threshold = 15000
    layer_meshes = {}

    for node, data in graph.nodes(data=True):
        x, y = np.array(data['points'][::2], dtype=np.float32), np.array(data['points'][1::2], dtype=np.float32)
        layer = data.get('layer')
        if layer not in selected_layers:
            continue

        base_z = layer_z_coordinates.get(layer, 0)
        if len(x) == 1 and len(y) == 1:
            x = np.append(x, x)
            y = np.append(y, y)

        if np.ptp(x) <= max_size_threshold and np.ptp(y) <= max_size_threshold and layer in available_layers:
            color = layer_colors.get(layer, 'white')
            if len(x) == 2 and len(y) == 2 and show_labels:
                bottom_points = np.array([
                    [x[0] - spike_width, y[0] - spike_width, base_z],
                    [x[0] + spike_width, y[0] - spike_width, base_z],
                    [x[0] + spike_width, y[0] + spike_width, base_z],
                    [x[0] - spike_width, y[0] + spike_width, base_z],
                    [x[1] - spike_width, y[1] - spike_width, base_z],
                    [x[1] + spike_width, y[1] - spike_width, base_z],
                    [x[1] + spike_width, y[1] + spike_width, base_z],
                    [x[1] - spike_width, y[1] + spike_width, base_z],
                ])
                top_points = bottom_points.copy()
                top_points[:, 2] = base_z + spike_thickness

                faces = []
                faces.extend([4, 0, 1, 2, 3])
                faces.extend([4, 4, 5, 6, 7])
                faces.extend([4, 8, 9, 10, 11])
                faces.extend([4, 12, 13, 14, 15])
                for i in range(4):
                    next_i = (i + 1) % 4
                    faces.extend([4, i, next_i, next_i + 8, i + 8])
                    faces.extend([4, i+4, (next_i+4), (next_i + 12), i + 12])

                mesh = pv.PolyData(np.vstack([bottom_points, top_points]), np.array(faces))
            else:
                bottom_points = np.column_stack((x, y, np.full_like(x, base_z)))
                top_points = np.column_stack((x, y, np.full_like(x, base_z + layer_thickness)))
                all_points = np.vstack([bottom_points, top_points])

                num_points = len(x)
                bottom_face = np.append(num_points, np.arange(num_points))
                top_face = np.append(num_points, np.arange(num_points) + num_points)

                side_faces = []
                for i in range(num_points):
                    next_i = (i + 1) % num_points
                    side_faces.extend([4, i, next_i, next_i + num_points, i + num_points])

                faces = np.concatenate([bottom_face, top_face, side_faces])
                mesh = pv.PolyData(all_points, faces)
                mesh = mesh.triangulate()

            if layer not in layer_meshes:
                layer_meshes[layer] = []
            layer_meshes[layer].append(mesh)

    for layer in available_layers:
        if layer in layer_meshes:
            combined_mesh = layer_meshes[layer][0]
            for mesh in layer_meshes[layer][1:]:
                combined_mesh = combined_mesh.merge(mesh)

            plotter.add_mesh(
                combined_mesh,
                color=layer_colors[layer],
                show_edges=False,
                smooth_shading=False,
                opacity=opacity,
                specular=0.5,
                specular_power=15
            )

    camera = plotter.camera
    camera.position = (0, -1, 0)
    camera.focal_point = (0, 0, 0)
    camera.view_up = (0, 1, 0)
    plotter.camera = camera
    plotter.view_xy()
    plotter.camera.roll += 0
    
    plotter.add_axes()    
    plotter.show()

def start_gui():
    ctk.set_appearance_mode("light")
    ctk.set_default_color_theme("blue")

    root = ctk.CTk()
    root.title("Layer Selection")

    selected_layers = []
    upper_layer_order = ['M2', 'CM2', 'CPA', 'CNA', 'CPE', 'CNE']
    lower_layer_order = ['M1', 'CM1', 'KN', 'P', 'NA', 'SP', 'SN', 'SI', 'CSI']
    checkboxes = {}

    show_labels_var = ctk.BooleanVar(value=False)
    opacity_var = ctk.BooleanVar(value=False)
    opacity_slider_var = ctk.DoubleVar(value=1.0)

    def update_layers():
        selected_layers.clear()
        for layer, var in checkboxes.items():
            if var.get():
                selected_layers.append(layer)

        if show_labels_var.get():
            label_layers = ['C', 'E', 'S', 'TN', 'TP', 'X', 'Y', 'ZERO']
            for layer in label_layers:
                if layer not in selected_layers:
                    selected_layers.append(layer)
                    
        opacity = opacity_slider_var.get() if opacity_var.get() else 1.0
        graph = parse_cif_to_graph('resources/input/adder2.cif')
        create_3d_plot(graph, selected_layers, show_labels_var.get(), opacity)

    def select_all(checkbox_group):
        for var in checkbox_group.values():
            var.set(True)

    def unselect_all(checkbox_group):
        for var in checkbox_group.values():
            var.set(False)

    upper_label = ctk.CTkLabel(root, text="Верхний уровень (Металл и контакты):")
    upper_label.grid(row=0, column=0, columnspan=4, sticky='w', pady=(10, 0))

    upper_checkboxes = {}
    for index, layer in enumerate(upper_layer_order):
        var = ctk.BooleanVar(value=True)
        cb = ctk.CTkCheckBox(root, text=layer, variable=var)
        cb.grid(row=index // 4 + 1, column=index % 4, sticky='w')
        checkboxes[layer] = var
        upper_checkboxes[layer] = var

    upper_select_all_button = ctk.CTkButton(root, text="Выбрать все верхние", command=lambda: select_all(upper_checkboxes))
    upper_select_all_button.grid(row=5, column=0, columnspan=2, sticky='ew')

    upper_unselect_all_button = ctk.CTkButton(root, text="Снять выбор всех верхних", command=lambda: unselect_all(upper_checkboxes))
    upper_unselect_all_button.grid(row=5, column=2, columnspan=2, sticky='ew')

    lower_label = ctk.CTkLabel(root, text="Нижний уровень (Остальные слои):")
    lower_label.grid(row=6, column=0, columnspan=4, sticky='w', pady=(10, 0))

    lower_checkboxes = {}
    for index, layer in enumerate(lower_layer_order):
        var = ctk.BooleanVar(value=True)
        cb = ctk.CTkCheckBox(root, text=layer, variable=var)
        cb.grid(row=index // 4 + 7, column=index % 4, sticky='w')
        checkboxes[layer] = var
        lower_checkboxes[layer] = var

    lower_select_all_button = ctk.CTkButton(root, text="Выбрать все нижние", command=lambda: select_all(lower_checkboxes))
    lower_select_all_button.grid(row=12, column=0, columnspan=2, sticky='ew')

    lower_unselect_all_button = ctk.CTkButton(root, text="Снять выбор всех нижних", command=lambda: unselect_all(lower_checkboxes))
    lower_unselect_all_button.grid(row=12, column=2, columnspan=2, sticky='ew')
    
    opacity_var = ctk.BooleanVar(value=True)
    opacity_check = ctk.CTkCheckBox(root, text="Включить прозрачность", variable=opacity_var)
    opacity_check.grid(row=13, column=0, columnspan=2, sticky='w', pady=(10, 10))

    opacity_slider = ctk.CTkSlider(root, from_=0.0, to=1.0, number_of_steps=100, variable=opacity_slider_var)
    opacity_slider.grid(row=13, column=2, columnspan=2, sticky='ew', padx=10)
    opacity_slider.set(0.5)

    show_labels_cb = ctk.CTkCheckBox(root, text="Показать метки затворов", variable=show_labels_var)
    show_labels_cb.grid(row=14, column=0, columnspan=4, sticky='w')

    update_button = ctk.CTkButton(root, text="Построить график", command=update_layers)
    update_button.grid(row=15, column=0, columnspan=4, pady=(10, 10))

    root.mainloop()

if __name__ == '__main__':
    start_gui()
