from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QCheckBox, QPushButton, QLabel, QSlider, QScrollArea, QFileDialog, 
    QTextEdit
)
from PySide6.QtCore import Qt
import pyvista as pv
from pyvistaqt import QtInteractor
import networkx as nx
import numpy as np
import sys
import re
from src.circuits.verification import verification
from src.circuits.TopologicalCircuit import TopologicalCircuit

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
    collecting_polygon = False
    polygon_line = ''
    node_id = 0

    with open(filename, 'r') as file:
        for line in file:
            line = line.strip()
            if line.startswith('L '):
                current_layer = line.split()[1].replace(';', '')
            elif line.startswith('P ') or collecting_polygon:
                polygon_line += ' ' + line
                collecting_polygon = not polygon_line.strip().endswith(';')
                
                if not collecting_polygon:
                    points = tuple(map(int, re.findall(r'-?\d+', polygon_line)))
                    size_of_points = len(points)
                    if size_of_points >= 6 and size_of_points % 2 == 0:
                        graph.add_node(node_id, layer=current_layer, points=points)
                        node_id += 1

                    polygon_line = ''
                    
            elif line.startswith('4N '):
                parts = line.split()
                layer = re.sub(r'\d+', '', parts[1])
                points = tuple(map(int, [part.replace(';', '') for part in parts[2:]]))
                graph.add_node(node_id, layer=layer, points=points)
                node_id += 1

    return graph

def create_3d_plot(graph, selected_layers, show_labels, opacity=1.0, plotter=None, highlighted_polygons=[]):
    """Generates a 3D plot of the graph with selected layers, ensuring no gaps and grouping specific layers at the same level."""
    plotter = plotter
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
            for mesh in layer_meshes[layer]:
                plotter.add_mesh(
                    mesh,
                    color=layer_colors[layer],
                    show_edges=False,
                    line_width= 1,
                    opacity=opacity,
                    specular=0.5,
                    specular_power=15,
                    style='surface'
                )
    
    for poly_group, layer in highlighted_polygons:
        base_z = layer_z_coordinates.get(layer, 0)

        for contour in poly_group:
            x = np.array([pt[0] for pt in contour], dtype=np.float32)
            y = np.array([pt[1] for pt in contour], dtype=np.float32)

            bottom = np.column_stack((x, y, np.full_like(x, base_z, dtype=np.float32)))
            top = np.column_stack((x, y, np.full_like(x, base_z + layer_thickness + 1, dtype=np.float32)))
            all_points = np.vstack([bottom, top]).astype(np.float32)

            n = len(x)
            bottom_face = np.append(n, np.arange(n))
            top_face = np.append(n, np.arange(n) + n)

            side_faces = []
            for i in range(n):
                ni = (i + 1) % n
                side_faces.extend([4, i, ni, ni + n, i + n])

            faces = np.concatenate([bottom_face, top_face, side_faces])
            highlight_mesh = pv.PolyData(all_points, faces)
            highlight_mesh = highlight_mesh.triangulate()

            plotter.add_mesh(
                highlight_mesh,
                color='white',
                opacity=1.0,
                show_edges=False,
                line_width=2,
                style='surface',
                specular=1,
                specular_power=50
            )


    
    plotter.camera.roll += 0
    
    plotter.add_axes()    
    plotter.show()

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Layer Selection")
        self.setMinimumSize(1200, 800)

        self.plotter_widget = QtInteractor(self)
        self.selected_layers = set()
        self.layer_order = ['M2', 'CM2', 'CPA', 'CNA', 'CPE', 'CNE', 'M1', 'CM1', 'KN', 'P', 'NA', 'SP', 'SN', 'SI', 'CSI']
        self.checkbox_map = {}
        self.topological_circuit = TopologicalCircuit()

        main_layout = QHBoxLayout()
        
        # левая панель с файлами
        control_panel = QVBoxLayout()
        
        self.file_path_top = None
        self.open_file_button_top = QPushButton("Открыть CIF файл")
        self.open_file_button_top.clicked.connect(self.open_file_dialog_top)
        control_panel.addWidget(self.open_file_button_top)

        self.file_path_el = None
        self.open_file_button_el = QPushButton("Открыть net файл")
        self.open_file_button_el.clicked.connect(self.open_file_dialog_el)
        control_panel.addWidget(self.open_file_button_el)

        self.highlighted_polygons = []
        self.verify_button = QPushButton("Верифицировать схемы")
        self.verify_button.clicked.connect(self.verify_circuits)
        control_panel.addWidget(self.verify_button)

        self.result_log = QTextEdit()
        self.result_log.setReadOnly(True)
        control_panel.addWidget(self.result_log)
        control_panel.addStretch()

        # правая панель управления 3D
        plot_panel = QVBoxLayout()

        label = QLabel("Слои:")
        plot_panel.addWidget(label)

        scroll = QScrollArea()
        scroll_widget = QWidget()
        checkbox_layout = QVBoxLayout()

        for layer in self.layer_order:
            cb = QCheckBox(layer)
            cb.setChecked(True)
            cb.stateChanged.connect(self.update_selected_layers)
            self.checkbox_map[layer] = cb
            checkbox_layout.addWidget(cb)

        scroll_widget.setLayout(checkbox_layout)
        scroll.setWidget(scroll_widget)
        scroll.setWidgetResizable(True)
        scroll.setMaximumHeight(250)
        plot_panel.addWidget(scroll)

        self.show_labels_cb = QCheckBox("Показать метки затворов")
        plot_panel.addWidget(self.show_labels_cb)

        self.opacity_cb = QCheckBox("Включить прозрачность")
        self.opacity_cb.setChecked(True)
        plot_panel.addWidget(self.opacity_cb)

        self.opacity_slider = QSlider(Qt.Horizontal)
        self.opacity_slider.setRange(0, 100)
        self.opacity_slider.setValue(50)
        plot_panel.addWidget(self.opacity_slider)

        build_button = QPushButton("Обновить график")
        build_button.clicked.connect(self.build_plot)
        plot_panel.addWidget(build_button)

        plot_panel.addStretch()
        plot_layout = QHBoxLayout()
        plot_layout.addWidget(self.plotter_widget.interactor, 4)
        plot_layout.addLayout(plot_panel, 1)
        
        graphics_child_layout = QHBoxLayout()
        self.netlist_text = QTextEdit()
        self.netlist_text.setReadOnly(True)
        graphics_child_layout.addWidget(self.netlist_text, 1)

        graphics_layout = QVBoxLayout()
        graphics_layout.addLayout(plot_layout, 7)
        graphics_layout.addLayout(graphics_child_layout, 4)
        

        main_layout.addLayout(control_panel, 1)
        main_layout.addLayout(graphics_layout, 4)

        container = QWidget()
        container.setLayout(main_layout)
        self.setCentralWidget(container)

    def update_selected_layers(self):
        self.selected_layers = {layer for layer, cb in self.checkbox_map.items() if cb.isChecked()}

    def build_plot(self):
        if not self.file_path_top:
            self.result_log.append("Файл топологической схемы не выбран!")
            return

        self.update_selected_layers()
        if self.show_labels_cb.isChecked():
            self.selected_layers.update(['C', 'E', 'S', 'TN', 'TP', 'X', 'Y', 'ZERO'])
        opacity = self.opacity_slider.value() / 100.0 if self.opacity_cb.isChecked() else 1.0

        self.plotter_widget.clear()
        graph = parse_cif_to_graph(self.file_path_top)
        create_3d_plot(graph, self.selected_layers, self.show_labels_cb.isChecked(), opacity, self.plotter_widget, self.highlighted_polygons)
        self.plotter_widget.reset_camera()
        self.plotter_widget.update()

    
    def open_file_dialog_top(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Выберите CIF файл", "", "CIF Files (*.cif);;All Files (*)")
        if file_path:
            self.file_path_top = file_path
            self.build_plot()

    def open_file_dialog_el(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Выберите net файл", "", "net Files (*.net);;All Files (*)")
        if file_path:
            try:
                with open(file_path, 'r', encoding='utf-8') as file:
                    content = file.read()
                    self.netlist_text.setPlainText(content)
            except Exception as e:
                self.netlist_text.setPlainText("Файл не загружен")

    def verify_circuits(self):
        if not self.file_path_top:
            self.result_log.append("Файл топологической схемы не выбран!")
            return
        if not self.file_path_el:
            self.result_log.append("Файл электрической схемы не выбран!")
            return

        is_isomorphic, connections, time = verification(self.file_path_el, "Электрическая схема", self.file_path_top, "Топологическая схема")
        self.result_log.append("Результат верификации:")
        if is_isomorphic:
            self.result_log.append("Графы схем изоморфны.\n" + f"Время выполнения проверки: {time} секунд.")
        else:
            self.result_log.append("Графы схем не изоморфны.\n" + f"Время выполнения проверки: {time} секунд.")
            if connections:
                self.result_log.append("Найдена точка разрыва.")
                print(connections)
                self.highlighted_polygons = connections
                self.build_plot()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())