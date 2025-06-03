from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QCheckBox, QPushButton, QLabel, QSlider, QScrollArea, QFileDialog, 
    QTextEdit, QGridLayout, QGroupBox, QProgressBar
)
from PySide6.QtCore import Qt, QThread, Signal, QObject
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
import matplotlib.pyplot as plt
import pyvista as pv
from pyvistaqt import QtInteractor
import numpy as np
import sys
from src.circuits.verification import verification
from src.circuits.verification import search_subcircuit
from src.circuits.TopologicalCircuit import TopologicalCircuit


class MeshBuilderWorker(QObject):
    meshes_ready = Signal(list)  # [(mesh, color, opacity)]

    def __init__(self, layers, selected_layers, highlighted_polygons, opacity):
        super().__init__()
        self.layers = layers
        self.selected_layers = selected_layers
        self.highlighted_polygons = highlighted_polygons
        self.opacity = opacity

    def run(self):
        meshes = build_layer_meshes(
            self.layers,
            self.selected_layers,
            self.highlighted_polygons,
            self.opacity
        )
        self.meshes_ready.emit(meshes)


class CircuitLoaderWorker(QObject):
    finished = Signal(object) 
    error = Signal(str)

    def __init__(self, topological_circuit, file_path_top):
        super().__init__()
        self.topological_circuit = topological_circuit
        self.file_path_top = file_path_top

    def run(self):
        try:
            self.topological_circuit.clean()
            self.topological_circuit.load_CIF(self.file_path_top)
            self.topological_circuit.compile()
            self.finished.emit(self.topological_circuit)
        except Exception as e:
            self.error.emit(str(e))



def build_layer_meshes(layers, selected_layers, highlighted_polygons, opacity):
    layer_order = ['KN', 'P', 'NA', 'SP', 'SN', 'SI', 'CPE', 'CNE', 'CSI', 'CNA', 'CPA',
                   'M1', 'CM1', 'M2', 'CM2']
    layer_thickness = 50
    space_between_layer = 25

    layer_groups = {
        'group1': ['P', 'NA'],
        'group2': ['CNA', 'CPA'],
        'group3': ['CPE', 'CNE'],
        'group4': ['SP', 'SN', 'SI']
    }

    # Цвета слоев
    layer_colors = {
        'KN': [200, 0, 0], 'CM1': 'black', 'CM2': 'cyan', 'CSI': 'orange', 'P': 'blue',
        'NA': 'red', 'CPA': 'yellow', 'CNA': 'pink', 'CPE': 'brown', 'CNE': 'lightgreen',
        'SP': 'grey', 'SN': 'grey', 'SI': 'green', 'M1': 'magenta', 'M2': 'cyan',
        'C': 'violet', 'E': 'teal', 'S': 'olive', 'TN': 'maroon', 'TP': 'navy',
        'X': 'turquoise', 'Y': 'lime', 'ZERO': 'indigo'
    }

    # Упорядоченные слои
    available_layers = [layer for layer in layer_order if layer in selected_layers]
    order_dict = {name: idx for idx, name in enumerate(layer_order)}
    sorted_layers = sorted(layers, key=lambda l: order_dict.get(l.name, len(layer_order)))
    layer_z_coordinates = {}
    assigned_groups = {}
    current_level = 0

    for lname in available_layers:
        for layer in layers:
            if layer.name == lname:
                group = next((g for g, ls in layer_groups.items() if lname in ls), None)
                if group and group not in assigned_groups:
                    for gname in layer_groups[group]:
                        layer_z_coordinates[gname] = current_level
                    assigned_groups[group] = current_level
                    current_level += space_between_layer
                elif not group:
                    layer_z_coordinates[lname] = current_level
                    current_level += space_between_layer

    result_meshes = []

    # Генерация основных слоев
    for layer in sorted_layers:
        if layer.name not in selected_layers:
            continue

        base_z = layer_z_coordinates.get(layer.name, 0)
        color = layer_colors.get(layer.name, 'white')

        for polygon in layer.polygons:
            if polygon:
                pts = np.array([(pt[0], pt[1], base_z) for pt in polygon], dtype=np.float32)
                top = pts.copy()
                top[:, 2] += layer_thickness

                all_pts = np.vstack([pts, top])
                num_pts = len(pts)

                bottom_face = np.hstack([num_pts, np.arange(num_pts)])
                top_face = np.hstack([num_pts, np.arange(num_pts) + num_pts])
                sides = []
                for i in range(num_pts):
                    ni = (i + 1) % num_pts
                    sides.extend([4, i, ni, ni + num_pts, i + num_pts])

                faces = np.concatenate([bottom_face, top_face, sides])
                mesh = pv.PolyData(all_pts, faces).triangulate()

                result_meshes.append((mesh, color, opacity))

    # Выделенные полигоны
    for poly_group, lname in highlighted_polygons:
        base_z = layer_z_coordinates.get(lname, 0)
        for contour in poly_group:
            x = np.array([pt[0] + 1 for pt in contour], dtype=np.float32)
            y = np.array([pt[1] + 1 for pt in contour], dtype=np.float32)

            bottom = np.column_stack((x, y, np.full_like(x, base_z)))
            top = np.column_stack((x, y, np.full_like(x, base_z + layer_thickness + 5)))

            all_pts = np.vstack([bottom, top])
            n = len(x)

            bottom_face = np.append(n, np.arange(n))
            top_face = np.append(n, np.arange(n) + n)

            sides = []
            for i in range(n):
                ni = (i + 1) % n
                sides.extend([4, i, ni, ni + n, i + n])

            faces = np.concatenate([bottom_face, top_face, sides])
            mesh = pv.PolyData(all_pts, faces).triangulate()

            result_meshes.append((mesh, 'white', 1.0))

    return result_meshes


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

        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 1)  
        self.progress_bar.setValue(0)
        self.progress_bar.setMaximumHeight(12)
        self.progress_bar.setTextVisible(False)
        
        
        main_layout = QVBoxLayout()
        main_layout.addLayout(self.plot_layout, 7)
        main_layout.addLayout(self.graphics_layout, 5)
        main_layout.addWidget(self.progress_bar)

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

        self.update_selected_layers()

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
        self.progress_bar.setRange(0, 0)
        self.progress_bar.setValue(0)
        self.thread = QThread()
        self.worker = MeshBuilderWorker(
            self.topological_circuit.layers,
            self.selected_layers,
            self.highlighted_polygons,
            self.opacity_slider.value() / 100
        )
        self.worker.moveToThread(self.thread)

        self.thread.started.connect(self.worker.run)
        self.worker.meshes_ready.connect(self.render_layer_meshes)
        self.worker.meshes_ready.connect(self.thread.quit)
        self.worker.meshes_ready.connect(self.worker.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)

        self.thread.start()

    def render_layer_meshes(self, meshes):
        self.plotter_widget.clear()
        self.plotter_widget.set_background("white", top="lightgray") 
        self.plotter_widget.enable_anti_aliasing("ssaa")
        self.plotter_widget.enable_depth_peeling(64)

        for mesh, color, opacity in meshes:
            self.plotter_widget.add_mesh(
                mesh,
                color=color,
                opacity=opacity,
                show_edges=False,
                style='surface',
                line_width=1
            )

        self.plotter_widget.add_axes()
        self.plotter_widget.reset_camera()
        self.plotter_widget.update()
        self.result_log.append("Построение завершено")
        self.progress_bar.setRange(0, 1)
        self.progress_bar.setValue(0)

    def show_plot_2D(self, subcircuits=[]):
        self.ax.clear()
        self.topological_circuit.visualize_trans(self.ax, subcircuits)
        self.canvas.draw()

    
    def open_file_dialog_top(self):
        self.progress_bar.setRange(0, 0)
        self.progress_bar.setValue(0)
        file_path, _ = QFileDialog.getOpenFileName(self, "Выберите CIF файл", "", "CIF Files (*.cif);;All Files (*)")
        if file_path:
            self.file_path_top = file_path
            self.result_log.append(f"Компиляция схемы из файла {file_path}")
            self.highlighted_polygons = []
            self.highlighted_elements = []
            self.topo_thread = QThread()
            self.topo_worker = CircuitLoaderWorker(self.topological_circuit, self.file_path_top)
            self.topo_worker.moveToThread(self.topo_thread)

            self.topo_thread.started.connect(self.topo_worker.run)
            self.topo_worker.finished.connect(self.on_topo_loaded)
            self.topo_worker.error.connect(self.on_topo_load_error)
            self.topo_worker.finished.connect(self.topo_thread.quit)
            self.topo_worker.finished.connect(self.topo_worker.deleteLater)
            self.topo_thread.finished.connect(self.topo_thread.deleteLater)

            self.topo_thread.start()
        else:
            self.progress_bar.setRange(0, 1)
            self.progress_bar.setValue(0)

    def on_topo_loaded(self, topo):
        self.result_log.append("Топологическая схема загружена и скомпилирована.")
        self.topological_circuit = topo
        self.progress_bar.setRange(0, 1)
        self.progress_bar.setValue(0)
        self.show_plot_2D()
        self.show_plot_3D()

    def on_topo_load_error(self, message):
        self.result_log.append(f"Ошибка загрузки схемы: {message}")
        self.progress_bar.setRange(0, 1)
        self.progress_bar.setValue(0)

    def open_file_dialog_el(self):
        self.progress_bar.setRange(0, 0)
        self.progress_bar.setValue(0)
        file_path, _ = QFileDialog.getOpenFileName(self, "Выберите net файл", "", "net Files (*.net);;All Files (*)")
        if file_path:
            try:
                with open(file_path, 'r', encoding='utf-8') as file:
                    content = file.read()
                    netlist_name = file_path.split('/')[-1]
                    self.netlist_name.setText(f"Название: {netlist_name}")
                    self.netlist_text.setPlainText(content)
                    self.file_path_el = file_path
                    self.result_log.append(f"Загружен файл электрической схемы {file_path}")
            except Exception as e:
                self.netlist_text.setPlainText("Файл не загружен")

        self.progress_bar.setRange(0, 1)
        self.progress_bar.setValue(0)

    def verify_circuits(self):
        if not self.file_path_top:
            self.result_log.append("Файл топологической схемы не выбран!")
            return
        if not self.file_path_el:
            self.result_log.append("Файл электрической схемы не выбран!")
            return
        
        self.progress_bar.setRange(0, 0)
        self.progress_bar.setValue(0)
        self.highlighted_polygons = []
        self.highlighted_elements = []
        is_isomorphic, connections, time = verification(self.file_path_el, "Электрическая схема", topological_circuit=self.topological_circuit)
        self.result_log.append("Результат верификации:")
        self.progress_bar.setRange(0, 1)
        self.progress_bar.setValue(0)
        if is_isomorphic:
            self.result_log.append("Графы схем изоморфны.\n" + f"Время выполнения проверки: {time} секунд.")
        else:
            self.result_log.append("Графы схем не изоморфны.\n" + f"Время выполнения проверки: {time} секунд.")
            if connections:
                self.result_log.append("Найдена точка разрыва.")
                self.highlighted_polygons = [self.topological_circuit.get_polygons(id) for id in connections]
                self.highlighted_elements = connections
                self.show_plot_3D()
    
    def search_subcircuits(self):
        if not self.file_path_top:
            self.result_log.append("Файл топологической схемы не выбран!")
            return
        if not self.file_path_el:
            self.result_log.append("Файл электрической схемы не выбран!")
            return
        self.progress_bar.setRange(0, 0)
        self.progress_bar.setValue(0)
        self.subcircuits = []
        subcircuits, time = search_subcircuit(self.file_path_el, "Электрическая схема", topological_circuit=self.topological_circuit)
        self.progress_bar.setRange(0, 1)
        self.progress_bar.setValue(0)
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