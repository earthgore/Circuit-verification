import matplotlib.pyplot as plt
from math import atan2
from matplotlib.patches import Polygon
import intersection_cpp

class Layer:
    def __init__(self, name, points=None):
        self.name = name
        self.polygons = []
        if points is not None:
            self.polygons.append(points)


    def add_polygon(self, points):
        self.polygons.append(points)
        
    
    def delete_duplicate(self):
        self.polygons = list(set([tuple(polygon) for polygon in self.polygons]))
        self.polygons = list(map(list, self.polygons))


    def plot(self, ax, color='blue', alpha=0.5):
        for polygon in self.polygons:
            ax.add_patch(Polygon(polygon, closed=True, fill=True, color=color, alpha=alpha))


    def do_lines_intersect(self, p1, p2, q1, q2):
        
        return intersection_cpp.do_lines_intersect(p1, p2, q1, q2);'''
        def orientation(p, q, r):
            val = (q[1] - p[1]) * (r[0] - q[0]) - (q[0] - p[0]) * (r[1] - q[1])
            if val == 0:
                return 0
            return 1 if val > 0 else 2

        def get_intersection_point(p1, p2, q1, q2):
            def line_coefficients(p1, p2):
                A = p2[1] - p1[1]
                B = p1[0] - p2[0]
                C = A * p1[0] + B * p1[1]
                return A, B, C

            A1, B1, C1 = line_coefficients(p1, p2)
            A2, B2, C2 = line_coefficients(q1, q2)

            determinant = A1 * B2 - A2 * B1

            if determinant == 0:
                return None  # Линии параллельны

            x = (B2 * C1 - B1 * C2) / determinant
            y = (A1 * C2 - A2 * C1) / determinant
            return (x, y)

        o1 = orientation(p1, p2, q1)
        o2 = orientation(p1, p2, q2)
        o3 = orientation(q1, q2, p1)
        o4 = orientation(q1, q2, p2)

        if o1 != o2 and o3 != o4:
            return True, get_intersection_point(p1, p2, q1, q2)

        def on_segment(p, q, r):
            if q[0] <= max(p[0], r[0]) and q[0] >= min(p[0], r[0]) and q[1] <= max(p[1], r[1]) and q[1] >= min(p[1], r[1]):
                return True
            return False

        if o1 == 0 and on_segment(p1, q1, p2):
            return True, q1
        if o2 == 0 and on_segment(p1, q2, p2):
            return True, q2
        if o3 == 0 and on_segment(q1, p1, q2):
            return True, p1
        if o4 == 0 and on_segment(q1, p2, q2):
            return True, p2

        return False, None'''


    def get_intersection_points(self, polygon1, polygon2):
        n1 = len(polygon1)
        n2 = len(polygon2)
        intersections = []
        for i in range(n1):
            for j in range(n2):
                intersect, point = self.do_lines_intersect(polygon1[i], polygon1[(i + 1) % n1], polygon2[j], polygon2[(j + 1) % n2])
                if intersect:
                    intersections.append(point)
        return intersections


    def is_point_inside_polygon(self, point, polygon):
        return intersection_cpp.is_point_inside_polygon(point, polygon);
        """x, y = point
        n = len(polygon)
        inside = False

        p1x, p1y = polygon[0]
        for i in range(n + 1):
            p2x, p2y = polygon[i % n]
            
            # Проверка, находится ли точка на ребре многоугольника
            if ((p1x == p2x and p1x == x and y >= min(p1y, p2y) and y <= max(p1y, p2y)) or
                (p1y == p2y and p1y == y and x >= min(p1x, p2x) and x <= max(p1x, p2x)) or
                ((x - p1x) * (p2y - p1y) == (y - p1y) * (p2x - p1x) and
                x >= min(p1x, p2x) and x <= max(p1x, p2x) and
                y >= min(p1y, p2y) and y <= max(p1y, p2y))):
                return False
            
            # Проверяем, находится ли точка между y-координатами ребра многоугольника
            if y > min(p1y, p2y):
                if y <= max(p1y, p2y):
                    if x <= max(p1x, p2x):
                        if p1y != p2y:
                            # Вычисляем x-координату точки пересечения
                            xinters = (y - p1y) * (p2x - p1x) / (p2y - p1y) + p1x
                        if p1x == p2x or x <= xinters:
                            # Переключаем флаг inside
                            inside = not inside
            p1x, p1y = p2x, p2y
        
        return inside"""


    def get_polygons_intersection(self, polygon1, polygon2): 
        intersections = self.get_intersection_points(polygon1, polygon2)

        for point in polygon1:
            if self.is_point_inside_polygon(point, polygon2):
                intersections.append(point)
        for point in polygon2:
            if self.is_point_inside_polygon(point, polygon1):
                intersections.append(point)

        if not intersections:
            return []

        intersections = list(set([tuple(map(int, point)) for point in intersections]))
        
        return self.sort_points_in_polygon(intersections)


    def subtract_polygon(self, polygon1, polygon2):
        intersections = self.get_polygons_intersection(polygon1, polygon2)

        if not intersections:
            return polygon1

        result_polygon = []
        for point in polygon1:
            if not self.is_point_inside_polygon(point, polygon2):
                result_polygon.append(point)
        for point in intersections:
            if not self.is_point_inside_polygon(point, polygon2):
                result_polygon.append(point)

        result_polygon = list(set([tuple(map(int, point)) for point in result_polygon]))
        
        return self.sort_points_in_polygon(result_polygon)
    

    def sort_points_in_polygon(self, polygon):
        if polygon:
            center_x = sum([point[0] for point in polygon]) / len(polygon)
            center_y = sum([point[1] for point in polygon]) / len(polygon)
            def angle_from_center(point):
                return atan2(point[1] - center_y, point[0] - center_x)

            polygon.sort(key=angle_from_center)
        return polygon


    def split_polygon(self, polygon):
        n = len(polygon)
        for i in range(n):
            for j in range(i+1, n):
                for k in range(j+1, n):
                    for l in range(k+1, n):
                        new_polygon1 = [polygon[i], polygon[j], polygon[k], polygon[l]]
                        new_polygon2 = [polygon[m] for m in range(n) if m not in [i, j, k, l]]
                        if not (polygon[i][0] == polygon[j][0] and polygon[j][0] == polygon[k][0] or polygon[i][0] == polygon[j][0] and polygon[j][0] == polygon[l][0] or polygon[i][0] == polygon[k][0] and polygon[k][0] == polygon[l][0] or polygon[j][0] == polygon[k][0] and polygon[k][0] == polygon[l][0] or polygon[i][1] == polygon[j][1] and polygon[j][1] == polygon[k][1] or polygon[i][1] == polygon[j][1] and polygon[j][1] == polygon[l][1] or polygon[i][1] == polygon[k][1] and polygon[k][1] == polygon[l][1] or polygon[j][1] == polygon[k][1] and polygon[k][1] == polygon[l][1]):
                            if not self.get_intersection_points(new_polygon1, new_polygon2):
                                return self.sort_points_in_polygon(new_polygon1), self.sort_points_in_polygon(new_polygon2)
        
        return None, None


def visualize_intersection(layer1, layer2):
    fig, ax = plt.subplots()
    layer1.plot(ax, color='blue', alpha=0.5)
    layer2.plot(ax, color='red', alpha=0.5)

    for polygon1 in layer1.polygons:
        for polygon2 in layer2.polygons:
            intersection_area = layer1.get_polygons_intersection(polygon1, polygon2)
            if intersection_area:
                ax.add_patch(Polygon(intersection_area, closed=True, fill=True, color='green', alpha=0.5))
                
    ax.set_aspect('equal')
    ax.set_xlim([-1, 5000])
    ax.set_ylim([-1, 5000])
    plt.show()


def visualize_subtraction(layer1, layer2):
    fig, ax = plt.subplots()
    layer1.plot(ax, color='blue', alpha=0.5)
    layer2.plot(ax, color='red', alpha=0.5)

    for polygon1 in layer1.polygons:
        for polygon2 in layer2.polygons:
            result_polygon = layer1.subtract_polygon(polygon1, polygon2)
            if result_polygon:
                if len(result_polygon) == 8:
                    poly1, poly2 = layer1.split_polygon(result_polygon)
                    ax.add_patch(Polygon(poly1, closed=True, fill=True, color='yellow', alpha=0.5))
                    ax.add_patch(Polygon(poly2, closed=True, fill=True, color='yellow', alpha=0.5))
                    print(poly1, poly2)
                else:
                    ax.add_patch(Polygon(result_polygon, closed=True, fill=True, color='yellow', alpha=0.5))
                    print(result_polygon)

    ax.set_aspect('equal')
    ax.set_xlim([-100, 5000])
    ax.set_ylim([-100, 5000])
    plt.show()

