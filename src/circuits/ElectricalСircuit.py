from src.circuits.elements.Transistor import Transistor
from networkx import Graph
import json

class ElecrticalCircuit:
    def __init__(self, name):
        self.name = name
        self.id_counter = 0
        self.transistors = []
        self.buses = []
        self.nx_graph = Graph()

    def load_NET(self, filename):    
        with open(filename, 'r') as file:
            for line in file:
                split_line = line.split(" ")
                
                self.transistors.append(Transistor(split_line[2], split_line[3], split_line[1], split_line[0][1], self.id_counter))
                self.id_counter += 1


    def graph_nx_compile(self):
        for trans in self.transistors:
            self.nx_graph.add_node(trans.id, label=trans.type)
            for con in trans.connections:
                self.nx_graph.add_edge(trans.id, con, label="bus")
            for con in trans.gate_connections:
                self.nx_graph.add_edge(trans.id, con, label="gate")

        for bus in self.buses:
            self.nx_graph.add_node(bus[0], label="bus")
            for con in bus[2]:
                self.nx_graph.add_edge(bus[0], con, label="bus")


    def compile(self):
        for trans1 in self.transistors:
            for bus in self.buses:
                if bus[1] == trans1.drain:
                    bus[2].append(trans1.id)
                    break
            else:
                self.buses.append((self.id_counter, trans1.drain, [trans1.id]))
                self.id_counter += 1
            for bus in self.buses:
                if bus[1] == trans1.source:
                    bus[2].append(trans1.id)
                    break
            else:
                self.buses.append((self.id_counter, trans1.source, [trans1.id]))
                self.id_counter += 1
            for bus in self.buses:
                if bus[1] == trans1.gate:
                    trans1.gate_connections.add(bus[0])
                    break
            else:
                self.buses.append((self.id_counter, trans1.gate, []))
                trans1.gate_connections.add(self.id_counter)
                self.id_counter += 1

        self.graph_nx_compile()
            

    def graph_to_json(self, filename):
        nodes = []
        edges = []

        for trans in self.transistors:
            nodes.append({"id": trans.id, "name": trans.type + str(trans.id), "label": trans.type})
            for con in trans.connections:
                edges.append({"source": trans.id, "target": con, "label": "bus"})
            for con in trans.gate_connections:
                edges.append({"source": trans.id, "target": con, "label": "gate"})


        for bus in self.buses:
            nodes.append({"id": bus[0], "name": bus[1], "label" : "bus"})
            for con in bus[2]:
                edges.append({"source": bus[0], "target": con, "label": "bus"})


        graph = {
            "nodes": nodes,
            "edges": edges
        }

        graph_json = json.dumps(graph, indent=4)

        with open(filename, 'w') as file:
            file.write(graph_json)

