class Contact:
    def __init__(self, name, layer1, layer2, contact_polygon, layer_polygon, id):
        self.name = name
        self.layer1 = layer1
        self.layer2 = layer2
        self.contact_polygon = contact_polygon
        self.layer_polygon = layer_polygon
        self.id = id
        self.connections = set()
