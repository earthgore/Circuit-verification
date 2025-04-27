import json
import tkinter as tk
import networkx as nx
import customtkinter as ctk
import matplotlib.pyplot as plt
from timeit import default_timer as timer
from tkinter import filedialog
from networkx.algorithms import isomorphism
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
# Local imports
# from algo.color_refinement import color_refinement_isomorphism
# from algo.weisfeiler_lehman import weisfeiler_lehman_isomorphism

# High DPI settings fix

try:
    from ctypes import windll
    windll.shcore.SetProcessDpiAwareness(1)
except:
    pass

class LogColors:
    SUCCESS = "#28a745"
    MESSAGE = "#ffc107"
    FAILURE = "#dc3545"
    TEXT = "#ffffff"
    INFO = "#0a9bff"
    
class GraphDisplay:
    def __init__(self, master):
        self.master = master
    
    def display_graph(self, graph, frame, max_nodes=100, max_edges=200):
        for widget in frame.winfo_children():
            widget.destroy()
        
        num_nodes = len(graph.nodes())
        num_edges = len(graph.edges())
        
        if num_nodes > max_nodes or num_edges > max_edges:
            label = tk.Label(frame, text="Граф слишком объемный для его отображения.")
            label.grid(row=1, column=0, sticky="nsew")
        else:
            fig, ax = plt.subplots(figsize=(5.5, 5.5))
            pos = nx.spring_layout(graph)
            nx.draw(graph, pos, with_labels=True, labels=nx.get_node_attributes(graph, 'label'), ax=ax)
            canvas = FigureCanvasTkAgg(fig, master=frame)
            canvas.draw()
            canvas.get_tk_widget().grid(row=0, column=0, sticky="nsew")

class GraphIsomorphismCheckerApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("IsoGraphChecker")
        self.geometry("1430x590")
        self.resizable(False, False)

        # Store references to after callbacks
        self.after_callbacks = []
        graph_frame_width = graph_frame_height = 550
        controls_width = 250
        log_height = 360

        # Configure grid layout
        self.grid_columnconfigure(1, weight=1)
        self.grid_columnconfigure(2, weight=0)
        self.grid_rowconfigure(0, weight=1)

        # Frames for layout
        self.frame_controls = ctk.CTkFrame(self, width=controls_width+20)
        self.frame_controls.grid(row=0, column=0, padx=(10,0), pady=(10,10), sticky="nsew")
        self.frame_controls.grid_propagate(False)
        self.frame_graphs = ctk.CTkFrame(self, width=graph_frame_width+20, height=graph_frame_height+20)
        self.frame_graphs.grid(row=0, column=1, padx=(10,10), pady=(10,10), sticky="nsew")
        self.frame_graphs.grid_propagate(False)
        
        # Frames
        self.frame_graph1 = ctk.CTkFrame(self.frame_graphs, width=graph_frame_width, height=graph_frame_height)
        self.frame_graph1.grid(row=0, column=0, padx=(10,5), pady=(10,10), sticky="nsew")
        self.frame_graph1.grid_rowconfigure(1, weight=1)
        self.frame_graph1.grid_columnconfigure(0, weight=1)
        self.frame_graph1.grid_propagate(False)
        self.frame_graph2 = ctk.CTkFrame(self.frame_graphs, width=graph_frame_width, height=graph_frame_height)
        self.frame_graph2.grid(row=0, column=1, padx=(5,10), pady=(10,10), sticky="nsew")
        self.frame_graph2.grid_rowconfigure(1, weight=1)
        self.frame_graph2.grid_columnconfigure(0, weight=1)
        self.frame_graph2.grid_propagate(False)
        
        # Widgets in frames
        self.button_load1 = ctk.CTkButton(self.frame_controls, width=controls_width, text="Загрузить 1 схему (JSON)", command=self.load_graph1)
        self.button_load1.grid(row=0, column=0, padx=(10,10), pady=(10,10), sticky="nsew")
        self.button_load2 = ctk.CTkButton(self.frame_controls, width=controls_width, text="Загрузить 2 схему (JSON)", command=self.load_graph2)
        self.button_load2.grid(row=1, column=0, padx=(10,10), pady=(0,10), sticky="nsew")
        self.button_check = ctk.CTkButton(self.frame_controls, width=controls_width, text="Проверить на изоморфизм", command=self.check_isomorphism, fg_color="green")
        self.button_check.grid(row=3, column=0, padx=(10,10), pady=(0,10), sticky="nsew")
        self.log_widget = ctk.CTkTextbox(self.frame_controls, width=controls_width, wrap="word", state='disabled', height=log_height + 40)
        self.log_widget.grid(row=4, column=0, padx=(10,10), pady=(0,10), sticky="nsew")
        self.log_widget.grid_propagate(False)
        self.button_clear_log = ctk.CTkButton(self.frame_controls, width=controls_width, text="Очистить лог", command=self.clear_log)
        self.button_clear_log.grid(row=5, column=0, padx=(10,10), pady=(0,10), sticky="nsew")
        self.label_graph1 = ctk.CTkLabel(self.frame_graph1, text="Чтобы загрузить граф схемы 1\n" + 
                                                                 "для дальнейшей проверки на изоморфизм, \n" +
                                                                 "нажмите на кнопку «Загрузить схему 1 (JSON)».")
        self.label_graph1.grid(row=1, column=0, sticky="nsew")
        self.label_graph2 = ctk.CTkLabel(self.frame_graph2, text="Чтобы загрузить граф схемы 2\n" + 
                                                                 "для дальнейшей проверки на изоморфизм, \n" +
                                                                 "нажмите на кнопку «Загрузить схему 2 (JSON)».")
        self.label_graph2.grid(row=1, column=0, sticky="nsew")

        # Configure log text tags for colors
        self.log_widget.tag_config("SUCCESS", foreground=LogColors.SUCCESS) 
        self.log_widget.tag_config("FAILURE", foreground=LogColors.FAILURE)
        self.log_widget.tag_config("TEXT", foreground=LogColors.TEXT)
        self.log_widget.tag_config("MESSAGE", foreground=LogColors.MESSAGE)
        self.log_widget.tag_config("INFO", foreground=LogColors.INFO)
        self.log("Данная программа предназначена для проверки графов на изоморфность", "INFO")
        self.log("Для начала работы сперва загрузите два графа с помощью кнопок выше.", "TEXT")
        self.graph1 = None
        self.graph2 = None

    def load_graph1(self):
        file_path = filedialog.askopenfilename(filetypes=[("JSON files", "*.json")])
        if file_path:
            with open(file_path, "r") as f:
                data = json.load(f)
                self.graph1 = self.create_graph(data)
                GraphDisplay.display_graph(self, self.graph1, self.frame_graph1)
            self.log(f"Граф 1 загружен из файла {file_path}", "MESSAGE")
        else:
            self.log("Загрузка графа 1 отменена.", "MESSAGE")

    def load_graph2(self):
        file_path = filedialog.askopenfilename(filetypes=[("JSON files", "*.json")])
        if file_path:
            with open(file_path, "r") as f:
                data = json.load(f)
                self.graph2 = self.create_graph(data)
                GraphDisplay.display_graph(self, self.graph2, self.frame_graph2)
            self.log(f"Граф 2 загружен из файла {file_path}", "MESSAGE")
        else:
            self.log("Загрузка графа 2 отменена.", "MESSAGE")

    def create_graph(self, data):
        graph = nx.Graph()
        for node in data["nodes"]:
            graph.add_node(node["id"], label=node["label"])
        for edge in data["edges"]:
            graph.add_edge(edge["source"], edge["target"])
        return graph

    def check_isomorphism(self):
        self.log("Проверка на изоморфизм...", "TEXT")
        if self.graph1 is None or self.graph2 is None:
            self.log("Оба графа должны быть сперва загружены!", "FAILURE")
            return
        
        start_time = timer()
        isomorphic = isomorphism.GraphMatcher(self.graph1, self.graph2)
        
        if isomorphic.is_isomorphic():
            self.log("Графы изоморфны!", "SUCCESS")
        else:
            self.log("Графы не изоморфны!", "FAILURE")

        end_time = timer()
        elapsed_time = end_time - start_time
        self.log(f"Время выполнения: {elapsed_time:.6f} секунд", "INFO")
        
    def log(self, message, tag):
        self.log_widget.configure(state='normal')
        self.log_widget.insert("end", message + "\n", tag)
        self.log_widget.see("end")
        self.log_widget.configure(state='disabled')

    def clear_log(self):
        self.log_widget.configure(state='normal')
        self.log_widget.delete('1.0', tk.END)
        self.log_widget.configure(state='disabled')

    def cancel_after_callbacks(self):
        for callback in self.after_callbacks:
            self.after_cancel(callback)
        self.after_callbacks.clear()

    def destroy(self):
        self.cancel_after_callbacks()   # Cancel all scheduled tasks
        self.quit()                     # Stops the mainloop
        super().destroy()               # Destroys the window and its children

if __name__ == "__main__":
    app = GraphIsomorphismCheckerApp()
    app.protocol("WM_DELETE_WINDOW", app.destroy)
    app.mainloop()
