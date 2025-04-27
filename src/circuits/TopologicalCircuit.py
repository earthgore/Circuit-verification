from re import findall as re_findall
from src.circuits.elements.Layer import Layer
from src.circuits.elements.Contact import Contact
from src.circuits.elements.Transistor import Transistor
from src.circuits.elements.Bus import Bus
import intersection_cpp as plgn
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon
import json

class TopologicalCircuit:
    def __init__(self, name):
        self.name = name
        self.id_counter = 0
        self.layers = []
        self.transistors = []
        self.contacts = []
        self.buses = []

        
    def load_CIF(self, filename):
        current_layer_name = None
        with open(filename, 'r') as file:
            for line in file:
                line = line.strip()
                if line.startswith('L '):
                    current_layer_name = line.split()[1].replace(';', '')
                elif line.startswith('P '):
                    points = tuple(map(int, re_findall(r'-?\d+', line)))
                    size_of_points = len(points)
                    if size_of_points >= 6 and size_of_points > 1 and size_of_points % 2 == 0:
                        for layer in self.layers:
                            if layer.name == current_layer_name:
                                layer.addPolygon([(points[i], points[i + 1]) for i in range(0, size_of_points, 2)])
                                break
                        else:
                            self.layers.append(Layer(current_layer_name, [(points[i], points[i + 1]) for i in range(0, size_of_points, 2)]))

        for layer in self.layers:
            layer.deleteDuplicate()


    def find_layer(self, layername):
        for layer in self.layers:
            if layer.name == layername:
                 return layer
        return None

    
    def find_all_transistors(self):
        SN_layer = self.find_layer("SN")
        NA_layer = self.find_layer("NA")
        if SN_layer is not None and NA_layer is not None:            
            for polygon in NA_layer.polygons:
                for gate in SN_layer.polygons:
                    if plgn.get_intersection_points(gate, polygon):
                        source, drain = plgn.split_polygon(plgn.subtract_polygon(polygon, gate))
                        if source and drain:
                            self.transistors.append(Transistor(gate, drain, source, "N", self.id_counter))
                            self.id_counter += 1
        
        SP_layer = self.find_layer("SP")
        NA_layer = self.find_layer("NA")
        if SP_layer is not None and NA_layer is not None:            
            for polygon in NA_layer.polygons:
                for gate in SP_layer.polygons:
                    if plgn.get_intersection_points(gate, polygon):
                        source, drain = plgn.split_polygon(plgn.subtract_polygon(polygon, gate))
                        if source and drain:
                            self.transistors.append(Transistor(gate, drain , source, "P", self.id_counter))
                            self.id_counter += 1


    def find_all_contacts(self):
        def find_cont(layer_contact, layer_name, melal_layer, contact_name):
            layer1 = self.find_layer(layer_contact)
            layer2 = self.find_layer(layer_name)
            layer3 = self.find_layer(melal_layer)
            if layer1 is not None and layer2 is not None and layer3 is not None:            
                for contact in layer1.polygons:
                    for polygon in layer2.polygons:
                        for M_contact in layer3.polygons:
                            if plgn.intersect_polygon(contact, polygon) and polygon == M_contact:
                                self.contacts.append(Contact(contact_name, layer_name, melal_layer, contact, polygon, self.id_counter))
                                self.id_counter += 1
                                break

        def find_cont_E(layer_contact, layer_name, melal_layer, contact_name):
            layer1 = self.find_layer(layer_contact)
            layer2 = self.find_layer(layer_name)
            layer3 = self.find_layer(melal_layer)
            if layer1 is not None and layer2 is not None and layer3 is not None:            
                for contact in layer1.polygons:
                    for polygon in layer2.polygons:
                        for M_contact in layer3.polygons:
                            if plgn.intersect_polygon(contact, polygon) and plgn.intersect_polygon(M_contact, polygon):
                                self.contacts.append(Contact(contact_name, layer_name, melal_layer, contact, polygon, self.id_counter))
                                self.id_counter += 1
                                break
        
        find_cont("CNA", "NA", "M1", "CN")
        find_cont("CPA", "NA", "M1", "CP")
        find_cont_E("CNE", "NA", "M1", "CNE")
        find_cont_E("CPE", "NA", "M1", "CPE")
        find_cont("CM1", "M1", "M2", "CM")
        find_cont("CSI", "SI", "M1", "CSI")


    def find_all_buses(self):
        def find_bus(layer_bus, bus_name):
            layer = self.find_layer(layer_bus)
            if layer is not None:            
                for bus in layer.polygons:
                    for contact in self.contacts:
                        if bus != contact.polygon_layer:
                            self.buses.append(Bus(bus_name, layer_bus, [bus], self.id_counter))
                            self.id_counter += 1
                            break
        
        find_bus("M1", "M1")
        find_bus("M2", "M2")
        find_bus("SI", "SI")


    def visualize_trans(self):
        fig, ax = plt.subplots()
        
        for i in range(len(self.transistors)):
            ax.add_patch(Polygon(self.transistors[i].source, closed=True, fill=True, color='yellow', alpha=0.4))
            ax.add_patch(Polygon(self.transistors[i].drain, closed=True, fill=True, color='red', alpha=0.4))
            ax.add_patch(Polygon(self.transistors[i].gate, closed=True, fill=True, color='blue', alpha=0.4))

        for i in range(len(self.contacts)):
            ax.add_patch(Polygon(self.contacts[i].polygon_contact, closed=True, fill=True, color='cyan', alpha=0.6))
 
        for i in range(len(self.buses)):
            if self.buses[i].id in [119, 162]:
                for poly in self.buses[i].polygons:
                    ax.add_patch(Polygon(poly, closed=True, fill=True, color=f"#B{i%10}8{i%10}C{i%10}", alpha=0.7))
                    print(self.buses[i].id)
                    print(poly)
            else:
                for poly in self.buses[i].polygons:
                    ax.add_patch(Polygon(poly, closed=True, fill=True, color=f"#B{i%10}8{i%10}C{i%10}", alpha=0.2))

        ax.set_aspect('equal')
        ax.set_xlim([-400, 8000])
        ax.set_ylim([-400, 5000])
        plt.show()


    def unite_buses(self):
        new_buses = []
        while self.buses:
            j = 0
            while j < len(self.buses):
                if self.buses[0] != self.buses[j] and self.buses[0].layer == self.buses[j].layer:
                    flag = False
                    for poly1 in self.buses[0].polygons:
                        for poly2 in self.buses[j].polygons:
                            if poly1 == poly2 or plgn.intersect_polygon(poly1, poly2):
                                self.buses[0].polygons.extend(self.buses[j].polygons)
                                flag = True
                                self.buses.pop(j)
                                j = -1
                                break
                        if flag:
                            break
                j += 1         
            new_buses.append(self.buses[0])
            self.buses.pop(0)
        self.buses = new_buses    
        

    def connect_bus_contact(self):
        for bus in self.buses:
            for contact in self.contacts:
                if (bus.layer == contact.layer1 or bus.layer == contact.layer2):
                    for poly in bus.polygons:
                        if plgn.intersect_polygon(poly, contact.polygon_contact):
                            contact.connections.add(bus.id)
                            break
    

    def connect_trans_contact(self):
        for trans in self.transistors:
            for contact in self.contacts:
                if contact.layer1 == "NA" and (plgn.intersect_polygon(trans.drain, contact.polygon_contact) or plgn.intersect_polygon(trans.source, contact.polygon_contact)):
                    contact.connections.add(trans.id)


    def connect_trans(self):
        for trans1 in self.transistors:
            for trans2 in self.transistors:
                for contact in self.contacts:
                    if contact.layer1 == "NA" and plgn.intersect_polygon(trans1.drain, contact.polygon_contact) and plgn.intersect_polygon(trans2.source, contact.polygon_contact):
                        break
                else:        
                    if plgn.intersect_polygon(trans1.drain, trans2.source):
                        self.buses.append(Bus("C", "NA", [], self.id_counter))
                        self.buses[-1].connections.add(trans2.id)
                        trans1.connections.add(self.id_counter)
                        self.id_counter += 1
                    

    def unite_gates_buses(self):
        new_buses = []
        for trans in self.transistors:
            bus = Bus("SI", "SI", [], self.id_counter)
            self.id_counter += 1
            flag = False
            j = 0
            while j < len(self.buses):
                if self.buses[j].layer == "SI":
                    for poly1 in self.buses[j].polygons:
                        if trans.gate not in self.buses[j].polygons and plgn.intersect_polygon(poly1, trans.gate):
                            bus.polygons.extend(self.buses[j].polygons)
                            bus.polygons.append(trans.gate)
                            self.buses.pop(j)
                            flag = True
                            j = -1
                            break
                j += 1
            if flag:
                new_buses.append(bus)  
        self.buses.extend(new_buses) 


    def connect_gate(self):
        for trans in self.transistors:
            for bus in self.buses:
                if bus.layer == "SI":
                    for poly in bus.polygons:
                        if poly == trans.gate or plgn.intersect_polygon(poly, trans.gate):
                            trans.gate_connections.add(bus.id)
                            break


    def merge_contact(self):
        for contact in self.contacts:
            for bus in self.buses:
                if bus.id in contact.connections:
                    bus.graph_connections = bus.graph_connections.union(contact.connections)
                    if bus.id in bus.graph_connections:
                        bus.graph_connections.remove(bus.id)


    def merge_M2(self):
        for bus_M2 in self.buses:
            for bus in self.buses:
                if bus_M2.layer == "M2" and (bus.id in bus_M2.graph_connections or bus_M2.id in bus.graph_connections):
                    bus_M2.graph_connections = bus_M2.graph_connections.union(bus.graph_connections)
                    if bus_M2.id in bus_M2.graph_connections:
                        bus_M2.graph_connections.remove(bus_M2.id)
                    if bus.id in bus_M2.graph_connections:
                        bus_M2.graph_connections.remove(bus.id)
                    bus.on_graph = False


    def merge_SI(self):
        for trans in self.transistors:
            for bus_SI in self.buses:
                for bus in self.buses:
                    if bus_SI.layer == "SI" and bus_SI.id in trans.gate_connections and (bus_SI.id in bus.graph_connections or bus.id in bus_SI.graph_connections):
                        trans.gate_connections.add(bus.id)
                        if bus_SI.id in trans.gate_connections: 
                            trans.gate_connections.remove(bus_SI.id)
                        if bus_SI.id in bus.graph_connections: 
                            bus.graph_connections.remove(bus_SI.id)
                        bus_SI.on_graph = False


    def compile(self):
        self.find_all_transistors()
        self.find_all_contacts()
        self.find_all_buses()

        self.unite_gates_buses()
        self.unite_buses()

        self.connect_bus_contact()
        self.connect_trans_contact()
        self.connect_trans()
        self.connect_gate()

    def graph_merge(self):
        for bus in self.buses:
                bus.graph_connections = bus.graph_connections.union(bus.connections)
        self.merge_contact()
        self.merge_M2()
        self.merge_SI()

    def graph_to_json(self, filename):
        self.graph_merge()

        nodes = []
        edges = []

        for trans in self.transistors:
            nodes.append({"id": trans.id, "name": trans.type + str(trans.id), "label": trans.type})
            for con in trans.connections:
                edges.append({"source": trans.id, "target": con})
            for con in trans.gate_connections:
                edges.append({"source": trans.id, "target": con})


        for bus in self.buses:
            if bus.on_graph:
                nodes.append({"id": bus.id, "name": bus.name + "_" + str(bus.id), "label": "bus"})
                for con in bus.graph_connections:
                    edges.append({"source": bus.id, "target": con})


        graph = {
            "nodes": nodes,
            "edges": edges
        }

        graph_json = json.dumps(graph, indent=4)

        with open(filename, 'w') as file:
            file.write(graph_json)

    



