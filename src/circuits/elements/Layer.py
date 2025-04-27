
class Layer:
    def __init__(self, name, points=None):
        self.name = name
        self.polygons = []
        if points is not None:
            self.polygons.append(points)


    def addPolygon(self, points):
        self.polygons.append(points)
        
    
    def deleteDuplicate(self):
        self.polygons = list(set([tuple(polygon) for polygon in self.polygons]))
        self.polygons = list(map(list, self.polygons))




    

