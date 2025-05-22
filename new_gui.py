from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QCheckBox, QPushButton, QLabel, QSlider, QScrollArea, QFileDialog, 
    QTextEdit, QGridLayout, QGroupBox
)
from PySide6.QtCore import Qt, QThread, Signal
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
import matplotlib.pyplot as plt
import pyvista as pv
from pyvistaqt import QtInteractor
import networkx as nx
import numpy as np
import sys
import re
from src.circuits.verification import verification
from src.circuits.verification import search_subcircuit
from src.circuits.TopologicalCircuit import TopologicalCircuit



def create_3d_plot(layers, selected_layers, opacity=1.0, plotter=None, highlighted_polygons=[]):
    """Generates a 3D plot of the graph with selected layers, ensuring no gaps and grouping specific layers at the same level."""
    plotter = plotter
    plotter.set_background("white", top="lightgray") 
    plotter.enable_anti_aliasing("ssaa")
    plotter.enable_depth_peeling(64)

    layer_order = ['KN', 'P', 'NA', 'SP', 'SN', 'SI', 'CPE', 'CNE', 'CSI', 'CNA', 'CPA', 
                   'M1', 'CM1', 'M2', 'CM2']
    layer_thickness = 50
    space_beteween_layer = 25

    # Сортируем слои в порядке layer_order
    available_layers = [layer for layer in layer_order if layer in selected_layers]
    if not available_layers:
        plotter.add_text("No layers selected", position='upper_edge', font_size=14)
        plotter.show()
        return

    # Определяем группы слоев
    layer_groups = {
        'group1': ['P', 'NA'],
        'group2': ['CNA', 'CPA'],
        'group3': ['CPE', 'CNE'],
        'group4': ['SP', 'SN', 'SI']
    }

    # Словарь для назначения уровней по Z для каждого слоя
    layer_z_coordinates = {}
    assigned_groups = {}
    current_level = 0

    # Назначаем уровни по Z
    for layer_name in available_layers:
        for layer in layers:
            if layer.name == layer_name and layer_name in available_layers:
                group = next((g for g, group_layers in layer_groups.items() if layer_name in group_layers), None)
                if group and group not in assigned_groups:
                    for glayer in layer_groups[group]:
                        layer_z_coordinates[glayer] = current_level
                    assigned_groups[group] = current_level
                    current_level += space_beteween_layer
                elif not group:
                    layer_z_coordinates[layer_name] = current_level
                    current_level += space_beteween_layer

    # Задание цветов слоев
    layer_colors = {
        'KN': [200, 0, 0], 'CM1': 'black', 'CM2': 'cyan', 'CSI': 'orange', 'P': 'blue',
        'NA': 'red', 'CPA': 'yellow', 'CNA': 'pink', 'CPE': 'brown', 'CNE': 'lightgreen',
        'SP': 'grey', 'SN': 'grey', 'SI': 'green', 'M1': 'magenta', 'M2': 'cyan',
        'C': 'violet', 'E': 'teal', 'S': 'olive', 'TN': 'maroon', 'TP': 'navy',
        'X': 'turquoise', 'Y': 'lime', 'ZERO': 'indigo'
    }

    # Построение слоев
    order_dict = {name: index for index, name in enumerate(layer_order)}
    sorted_layers = sorted(layers, key=lambda layer: order_dict.get(layer.name, len(layer_order)))

    for layer in sorted_layers:
        if layer.name not in selected_layers:
            continue

        base_z = layer_z_coordinates.get(layer.name, 0)
        color = layer_colors.get(layer.name, 'white')

        for polygon in layer.polygons:
            points = np.array([(pt[0], pt[1], base_z) for pt in polygon], dtype=np.float32)
            top_points = points.copy()
            top_points[:, 2] += layer_thickness

            all_points = np.vstack([points, top_points])
            num_points = len(polygon)

            # Формирование граней
            bottom_face = np.hstack([num_points, np.arange(num_points)])
            top_face = np.hstack([num_points, np.arange(num_points) + num_points])

            side_faces = []
            for i in range(num_points):
                ni = (i + 1) % num_points
                side_faces.extend([4, i, ni, ni + num_points, i + num_points])

            faces = np.concatenate([bottom_face, top_face, side_faces])
            mesh = pv.PolyData(all_points, faces)
            mesh = mesh.triangulate()

            plotter.add_mesh(
                mesh,
                color=color,
                opacity=opacity,
                show_edges=False,
                style='surface',
                line_width=1
            )

    
    for poly_group, layer in highlighted_polygons:
        base_z = layer_z_coordinates.get(layer, 0)

        for contour in poly_group:
            x = np.array([pt[0] + 1 for pt in contour], dtype=np.float32) 
            y = np.array([pt[1] + 1 for pt in contour], dtype=np.float32) 

            bottom = np.column_stack((x, y, np.full_like(x, base_z, dtype=np.float32)))
            top = np.column_stack((x, y, np.full_like(x, base_z + layer_thickness + 5, dtype=np.float32)))
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

    
    plotter.add_axes()    
    plotter.show()


class PlotterThread(QThread):
    finished = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.worker = parent

    def run(self):
        self.worker.show_plot_3D()
        self.finished.emit()


class MainWindow(QMainWindow):
    def __init__(self):
        self.selected_layers = set()
        self.layer_order = ['M2', 'CM2', 'CPA', 'CNA', 'CPE', 'CNE', 'M1', 'CM1', 'KN', 'P', 'NA', 'SP', 'SN', 'SI', 'CSI']
        self.layer_groups = {
            'Металл 2': ['M2', 'CM2'],
            'Металл 1': ['M1', 'CM1'],
            'Поликремний': ['SP', 'SN', 'SI', 'CSI'],
            'Контакты к активной области': ['CNA', 'CPA'],
            'Эквипотенциальные контакты': ['CPE', 'CNE'],
            'Активная область': ['P', 'NA'],
            'Карман' : ['KN']
        }
        
        self.topological_circuit = TopologicalCircuit()
        self.file_path_top = None
        self.file_path_el = None
        self.highlighted_polygons = []
        self.highlighted_elements = []
        self.subcircuits = []
        self.subcir_index = 0


    def init_ui(self):
        super().__init__()
        self.setWindowTitle("Layer Selection")
        self.setMinimumSize(1000, 700)
        

        self.init_plotter()
        self.init_control_panel()
        self.init_plot_layout()
        self.init_graphics_layout()
        
        main_layout = QVBoxLayout()
        main_layout.addLayout(self.plot_layout, 7)
        main_layout.addLayout(self.graphics_layout, 5)

        container = QWidget()
        container.setLayout(main_layout)
        self.setCentralWidget(container)


    def init_plotter(self):
        self.plotter_widget = QtInteractor(self)
        self.plotter_widget.set_background("white", top="lightgray") 
        self.plotter_widget.add_text("The circuit is not loaded", position='upper_edge', font_size=14)
        self.plotter_widget.show()
        self.plotter_widget.reset_camera()
        self.plotter_widget.update()

    def init_control_panel(self):
        # левая панель с файлами
        self.control_panel = QVBoxLayout()
        
        open_file_button_top = QPushButton("Открыть CIF файл")
        open_file_button_top.clicked.connect(self.open_file_dialog_top)
        self.control_panel.addWidget(open_file_button_top)

        open_file_button_el = QPushButton("Открыть net файл")
        open_file_button_el.clicked.connect(self.open_file_dialog_el)
        self.control_panel.addWidget(open_file_button_el)

        verify_button = QPushButton("Верифицировать схемы")
        verify_button.clicked.connect(self.verify_circuits)
        self.control_panel.addWidget(verify_button)

        log_label = QLabel("Логирование:")
        self.control_panel.addWidget(log_label)

        self.result_log = QTextEdit()
        self.result_log.setReadOnly(True)
        self.control_panel.addWidget(self.result_log)
        self.control_panel.addStretch()

    def init_plot_layout(self):
        plot_panel = QVBoxLayout()

        label = QLabel("Слои:")
        plot_panel.addWidget(label)

        scroll = QScrollArea()
        scroll_widget = QWidget()
        grid_layout = QVBoxLayout(scroll_widget)
        
        self.checkbox_map = {}
        max_columns = 2 

        # Добавляем группы чекбоксов
        for group_name, layers in self.layer_groups.items():
            group_box = QGroupBox(group_name)
            group_layout = QGridLayout(group_box)

            for index, layer in enumerate(layers):
                row = index // max_columns
                col = index % max_columns

                cb = QCheckBox(layer)
                cb.setChecked(True)
                cb.stateChanged.connect(self.update_selected_layers)
                self.checkbox_map[layer] = cb
                group_layout.addWidget(cb, row, col)

            grid_layout.addWidget(group_box)


        scroll.setWidget(scroll_widget)
        scroll.setWidgetResizable(True)
        plot_panel.addWidget(scroll)

        self.opacity_cb = QCheckBox("Включить прозрачность")
        self.opacity_cb.setChecked(True)
        plot_panel.addWidget(self.opacity_cb, 1)
        
        self.opacity_slider = QSlider(Qt.Horizontal)
        self.opacity_slider.setRange(0, 100)
        self.opacity_slider.setValue(50)
        plot_panel.addWidget(self.opacity_slider, 1)

        build_button = QPushButton("Обновить график")
        build_button.clicked.connect(self.show_plot_3D)
        plot_panel.addWidget(build_button, 1)

        plot_panel.addStretch()
        self.plot_layout = QHBoxLayout()
        self.plot_layout.addWidget(self.plotter_widget.interactor, 7)
        self.plot_layout.addLayout(plot_panel, 2)

    def init_graphics_layout(self):
        self.graphics_layout = QHBoxLayout()
        self.graphics_layout.addLayout(self.control_panel)
        netlist_layout = QVBoxLayout()
        self.netlist_name = QLabel("Название: файл не загружен")
        self.netlist_text = QTextEdit()
        self.netlist_text.setReadOnly(True)
        netlist_layout.addWidget(self.netlist_name, 1)
        netlist_layout.addWidget(self.netlist_text, 11)
        self.graphics_layout.addLayout(netlist_layout, 1)

        subcircuits_layout = QHBoxLayout()
        self.subcircuit_label = QLabel(f"Подсхема 0 из 0")
        subcircuits_layout.addWidget(self.subcircuit_label, 8)

        subcir_prev = QPushButton("←", self)
        subcir_prev.clicked.connect(self.prev_subcir)
        subcircuits_layout.addWidget(subcir_prev, 1)

        subcir_next = QPushButton("→", self)
        subcir_next.clicked.connect(self.next_subcir)
        subcircuits_layout.addWidget(subcir_next, 1)

        subcircuit_button = QPushButton("Найти подсхему")
        subcircuit_button.clicked.connect(self.search_subcircuits)
        subcircuits_layout.addWidget(subcircuit_button, 4)

        canvas_layout = QVBoxLayout()
        canvas_layout.addLayout(subcircuits_layout, 1)
        self.canvas = FigureCanvas(plt.Figure())
        canvas_layout.addWidget(self.canvas, 6)
        self.ax = self.canvas.figure.add_subplot(111)
        self.ax.axis('off')
        self.ax.text(0.5, 0.5, "Загрузите CIF файл", fontsize=14, ha='center', va='center', transform=self.ax.transAxes)

        self.graphics_layout.addLayout(canvas_layout, 2)


    def update_selected_layers(self):
        self.selected_layers = {layer for layer, cb in self.checkbox_map.items() if cb.isChecked()}

    def show_plot_3D(self):
        self.update_selected_layers()
        opacity = self.opacity_slider.value() / 100.0 if self.opacity_cb.isChecked() else 1.0

        self.plotter_widget.clear()
        
        create_3d_plot(self.topological_circuit.layers, self.selected_layers, opacity, self.plotter_widget, self.highlighted_polygons)
        self.plotter_widget.reset_camera()
        self.plotter_widget.update()


    def on_plot_finished(self):
        self.result_log.append("Построение завершено")

    def show_plot_2D(self, subcircuits=[]):
        self.ax.clear()
        self.topological_circuit.visualize_trans(self.ax, subcircuits)
        self.canvas.draw()

    
    def open_file_dialog_top(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Выберите CIF файл", "", "CIF Files (*.cif);;All Files (*)")
        if file_path:
            self.file_path_top = file_path
            self.topological_circuit.clean()
            self.topological_circuit.load_CIF(self.file_path_top)
            self.topological_circuit.compile()
            self.show_plot_3D()
            self.show_plot_2D()

    def open_file_dialog_el(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Выберите net файл", "", "net Files (*.net);;All Files (*)")
        if file_path:
            try:
                with open(file_path, 'r', encoding='utf-8') as file:
                    content = file.read()
                    netlist_name = file_path.split('/')[-1]
                    self.netlist_name.setText(f"Название: {netlist_name}")
                    self.netlist_text.setPlainText(content)
                    self.file_path_el = file_path
            except Exception as e:
                self.netlist_text.setPlainText("Файл не загружен")

    def verify_circuits(self):
        if not self.file_path_top:
            self.result_log.append("Файл топологической схемы не выбран!")
            return
        if not self.file_path_el:
            self.result_log.append("Файл электрической схемы не выбран!")
            return

        is_isomorphic, connections, time = verification(self.file_path_el, "Электрическая схема", topological_circuit=self.topological_circuit)
        self.result_log.append("Результат верификации:")
        if is_isomorphic:
            self.result_log.append("Графы схем изоморфны.\n" + f"Время выполнения проверки: {time} секунд.")
        else:
            self.result_log.append("Графы схем не изоморфны.\n" + f"Время выполнения проверки: {time} секунд.")
            if connections:
                self.result_log.append("Найдена точка разрыва.")
                self.highlighted_polygons = [self.topological_circuit.get_polygons(id) for id in connections]
                self.highlighted_elements = connections
                print(self.highlighted_elements)
                self.run_plot_3D_in_thread()
    
    def search_subcircuits(self):
        if not self.file_path_top:
            self.result_log.append("Файл топологической схемы не выбран!")
            return
        if not self.file_path_el:
            self.result_log.append("Файл электрической схемы не выбран!")
            return

        subcircuits, time = search_subcircuit(self.file_path_el, "Электрическая схема", topological_circuit=self.topological_circuit)
        self.result_log.append("Результат верификации:")
        if subcircuits:
            self.result_log.append("Подсхемы найдены.\n" + f"Время выполнения проверки: {time} секунд.")
            self.subcircuits = subcircuits
            self.subcircuit_label.setText(f"Подсхема {self.subcir_index + 1} из {len(self.subcircuits)}")
            if subcircuits:
                self.show_plot_2D(subcircuits[0])
            else:
                self.show_plot_2D()
        else:
            self.result_log.append("Подсхема не найдена.\n" + f"Время выполнения проверки: {time} секунд.")

    def prev_subcir(self):
        if self.subcir_index > 0:
            self.subcir_index -= 1
            self.subcircuit_label.setText(f"Подсхема {self.subcir_index + 1} из {len(self.subcircuits)}")
            self.show_plot_2D(self.subcircuits[self.subcir_index])

    def next_subcir(self):
        if self.subcir_index < len(self.subcircuits) - 1:
            self.subcir_index += 1
            self.subcircuit_label.setText(f"Подсхема {self.subcir_index + 1} из {len(self.subcircuits)}")
            self.show_plot_2D(self.subcircuits[self.subcir_index])


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.init_ui()
    window.show()
    sys.exit(app.exec())