from re import findall as re_findall
from src.circuits.elements.Layer import Layer
from src.circuits.elements.Contact import Contact
from src.circuits.elements.Transistor import Transistor
from src.circuits.elements.Bus import Bus
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon
import json

class TopologicalCircuit:
    def __init__(self, name, filename):
        self.name = name
        self.id_counter = 0
        self.layers = []
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
                                layer.add_polygon([(points[i], points[i + 1]) for i in range(0, size_of_points, 2)])
                                break
                        else:
                            self.layers.append(Layer(current_layer_name, [(points[i], points[i + 1]) for i in range(0, size_of_points, 2)]))

        for layer in self.layers:
            layer.delete_duplicate()


    def find_layer(self, layername):
        for layer in self.layers:
            if layer.name == layername:
                 return layer
        return None

    
    def transistor_finder(self):
        self.transistors = []
        SN_layer = self.find_layer("SN")
        NA_layer = self.find_layer("NA")
        if SN_layer is not None and NA_layer is not None:            
            for polygon in NA_layer.polygons:
                for gate in SN_layer.polygons:
                    if SN_layer.get_intersection_points(gate, polygon):
                        source, drain = SN_layer.split_polygon(SN_layer.subtract_polygon(polygon, gate))
                        if source and drain:
                            self.transistors.append(Transistor(gate, drain, source, "N", self.id_counter))
                            self.id_counter += 1
        
        SP_layer = self.find_layer("SP")
        NA_layer = self.find_layer("NA")
        if SP_layer is not None and NA_layer is not None:            
            for polygon in NA_layer.polygons:
                for gate in SP_layer.polygons:
                    if SP_layer.get_intersection_points(gate, polygon):
                        source, drain = SP_layer.split_polygon(SP_layer.subtract_polygon(polygon, gate))
                        if source and drain:
                            self.transistors.append(Transistor(gate, drain , source, "P", self.id_counter))
                            self.id_counter += 1


    def contact_finder(self):
        self.contacts = []
        def find_cont(layer_contact, layer_name, melal_layer, contact_name):
            layer1 = self.find_layer(layer_contact)
            layer2 = self.find_layer(layer_name)
            layer3 = self.find_layer(melal_layer)
            if layer1 is not None and layer2 is not None and layer3 is not None:            
                for contact in layer1.polygons:
                    for polygon in layer2.polygons:
                        for M_contact in layer3.polygons:
                            if layer1.get_polygons_intersection(contact, polygon) and polygon == M_contact:
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
                            if layer1.get_polygons_intersection(contact, polygon) and layer1.get_polygons_intersection(M_contact, polygon):
                                self.contacts.append(Contact(contact_name, layer_name, melal_layer, contact, polygon, self.id_counter))
                                self.id_counter += 1
                                break
        
        find_cont("CNA", "NA", "M1", "CN")
        find_cont("CPA", "NA", "M1", "CP")
        find_cont_E("CNE", "NA", "M1", "CNE")
        find_cont_E("CPE", "NA", "M1", "CPE")
        find_cont("CM1", "M1", "M2", "CM")
        find_cont("CSI", "SI", "M1", "CSI")


    def bus_finder(self):
        self.buses = []
        def find_bus(layer_bus, bus_name):
            layer = self.find_layer(layer_bus)
            if layer is not None:            
                for bus in layer.polygons:
                    for contact in self.contacts:
                        if bus != contact.layer_polygon:
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
            ax.add_patch(Polygon(self.contacts[i].contact_polygon, closed=True, fill=True, color='cyan', alpha=0.6))
 

        for i in range(len(self.buses)):
                for poly in self.buses[i].polygons:
                    ax.add_patch(Polygon(poly, closed=True, fill=True, color=f"#B{i%10}8{i%10}C{i%10}", alpha=0.2))



        ax.set_aspect('equal')
        ax.set_xlim([-400, 8000])
        ax.set_ylim([-400, 5000])
        plt.show()


    def bus_connection(self):
        new_buses = []
        while self.buses:
            j = 0
            while j < len(self.buses):
                if self.buses[0] != self.buses[j] and self.buses[0].layer == self.buses[j].layer:
                    flag = False
                    for poly1 in self.buses[0].polygons:
                        for poly2 in self.buses[j].polygons:
                            if poly1 == poly2 or self.find_layer(self.buses[0].layer).get_polygons_intersection(poly1, poly2):
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
        

    def bus_contact_connection(self):
        for bus in self.buses:
            for contact in self.contacts:
                if (bus.layer == contact.layer1 or bus.layer == contact.layer2):
                    for poly in bus.polygons:
                        if self.find_layer(bus.layer).get_polygons_intersection(poly, contact.contact_polygon):
                            contact.connections.add(bus.id)
                            break
    

    def trans_contact_connection(self):
        for trans in self.transistors:
            for contact in self.contacts:
                if contact.layer1 == "NA" and (self.find_layer("NA").get_polygons_intersection(trans.drain, contact.contact_polygon) or self.find_layer("NA").get_polygons_intersection(trans.source, contact.contact_polygon)):
                    contact.connections.add(trans.id)


    def trans_connection(self):
        for trans1 in self.transistors:
            for trans2 in self.transistors:
                for contact in self.contacts:
                    if contact.layer1 == "NA" and (self.find_layer("NA").get_polygons_intersection(trans1.drain, contact.contact_polygon) and self.find_layer("NA").get_polygons_intersection(trans2.source, contact.contact_polygon)):
                        break
                else:        
                    if self.find_layer("NA").get_polygons_intersection(trans1.drain, trans2.source):
                        self.buses.append(Bus("C", "NA", [], self.id_counter))
                        self.buses[-1].connections.add(trans2.id)
                        trans1.connections.add(self.id_counter)
                        self.id_counter += 1
                    

    def gate_bus_connection(self):
        new_buses = []
        for trans in self.transistors:
            bus = Bus("SI", "SI", [], self.id_counter)
            self.id_counter += 1
            flag = False
            j = 0
            while j < len(self.buses):
                if self.buses[j].layer == "SI":
                    for poly1 in self.buses[j].polygons:
                        if trans.gate not in self.buses[j].polygons and self.find_layer("SI").get_polygons_intersection(poly1, trans.gate):
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


    def gate_connection(self):
        for trans in self.transistors:
            for bus in self.buses:
                if bus.layer == "SI":
                    for poly in bus.polygons:
                        if poly == trans.gate or self.find_layer(bus.layer).get_polygons_intersection(poly, trans.gate):
                            trans.gate_connections.add(bus.id)
                            break


    def contact_merge(self):
        for contact in self.contacts:
            for bus in self.buses:
                if bus.id in contact.connections:
                    bus.connections = bus.connections.union(contact.connections)
                    if bus.id in bus.connections:
                        bus.connections.remove(bus.id)


    def M2_merge(self):
        for bus_M2 in self.buses:
            for bus in self.buses:
                if bus_M2.layer == "M2" and (bus.id in bus_M2.connections or bus_M2.id in bus.connections):
                    bus_M2.connections = bus_M2.connections.union(bus.connections)
                    if bus_M2.id in bus_M2.connections:
                        bus_M2.connections.remove(bus_M2.id)
                    if bus.id in bus_M2.connections:
                        bus_M2.connections.remove(bus.id)
                    bus.on_graph = False


    def SI_merge(self):
        for trans in self.transistors:
            for bus_SI in self.buses:
                for bus in self.buses:
                    if bus_SI.layer == "SI" and bus_SI.id in trans.gate_connections and (bus_SI.id in bus.connections or bus.id in bus_SI.connections):
                        trans.gate_connections.add(bus.id)
                        if bus_SI.id in trans.gate_connections: 
                            trans.gate_connections.remove(bus_SI.id)
                        if bus_SI.id in bus.connections: 
                            bus.connections.remove(bus_SI.id)
                        bus_SI.on_graph = False


    def setUp(self):
        self.transistor_finder()
        self.contact_finder()
        self.bus_finder()
        self.gate_bus_connection()
        self.bus_connection()
        self.bus_contact_connection()
        self.trans_contact_connection()
        self.trans_connection()
        self.gate_connection()


    def graphToJSON(self, filename):
        
        self.contact_merge()
        self.M2_merge()
        self.SI_merge()

        nodes = []
        edges = []

        for trans in self.transistors:
            nodes.append({"id": trans.id, "label": trans.type + str(trans.id)})
            for con in trans.connections:
                edges.append({"source": trans.id, "target": con})
            for con in trans.gate_connections:
                edges.append({"source": trans.id, "target": con})


        for bus in self.buses:
            if bus.on_graph:
                nodes.append({"id": bus.id, "label": bus.name + "_" + str(bus.id)})
                for con in bus.connections:
                    edges.append({"source": bus.id, "target": con})


        graph = {
            "nodes": nodes,
            "edges": edges
        }

        graph_json = json.dumps(graph, indent=4)

        with open(filename, 'w') as file:
            file.write(graph_json)

    



