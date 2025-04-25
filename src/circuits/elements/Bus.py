class Bus:
    def __init__(self, name, layer, polygons, id):
        self.name = name
        self.layer = layer
        self.polygons = polygons
        self.id = id
        self.connections = set()
        self.on_graph = True