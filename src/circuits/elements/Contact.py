class Contact:
    def __init__(self, name, layer1, layer2, contact_polygon, layer_polygon, id):
        self.name = name
        self.layer1 = layer1
        self.layer2 = layer2
        self.polygon_contact = contact_polygon
        self.polygon_layer = layer_polygon
        self.id = id
        self.connections = set()
        
