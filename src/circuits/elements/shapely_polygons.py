from shapely.geometry import Polygon as ShapelyPolygon, Point as ShapelyPoint
from shapely.ops import unary_union
from math import atan2
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon as MplPolygon


def do_lines_intersect(p1, p2, q1, q2):
    # Не нужен больше вручную — теперь всё делаем через Shapely
    raise NotImplementedError("Эта функция больше не используется с Shapely")


def get_intersection_points(polygon1, polygon2):
    if len(polygon1) < 3 or len(polygon2) < 3:
        return []

    try:
        poly1 = ShapelyPolygon(polygon1)
        poly2 = ShapelyPolygon(polygon2)

        if not poly1.is_valid or not poly2.is_valid:
            return []

        inter = poly1.intersection(poly2)

        points = []
        if inter.is_empty:
            return []

        if inter.geom_type == 'Point':
            points.append((inter.x, inter.y))
        elif inter.geom_type == 'MultiPoint':
            points = [(p.x, p.y) for p in inter.geoms]
        elif inter.geom_type == 'LineString':
            points = list(inter.coords)
        elif inter.geom_type in ('Polygon', 'MultiPolygon'):
            if inter.geom_type == 'Polygon':
                points = list(inter.exterior.coords)
            else:
                for g in inter.geoms:
                    points.extend(list(g.exterior.coords))

        return list(set([(int(x), int(y)) for x, y in points]))

    except Exception as e:
        print(f"[Ошибка при пересечении]: {e}")
        return []



def is_point_inside_polygon(point, polygon):
    return ShapelyPolygon(polygon).contains(ShapelyPoint(point))


def intersect_polygon(polygon1, polygon2):
    poly1 = ShapelyPolygon(polygon1)
    poly2 = ShapelyPolygon(polygon2)
    inter = poly1.intersection(poly2)

    if inter.is_empty:
        return []

    if inter.geom_type == 'Polygon':
        coords = list(inter.exterior.coords)
    elif inter.geom_type == 'MultiPolygon':
        coords = []
        for g in inter.geoms:
            coords.extend(list(g.exterior.coords))
    else:
        return []

    coords = [(int(x), int(y)) for x, y in coords]
    return coords


def subtract_polygon(polygon1, polygon2):
    poly1 = ShapelyPolygon(polygon1)
    poly2 = ShapelyPolygon(polygon2)
    diff = poly1.difference(poly2)

    if diff.is_empty:
        return []

    coords = []
    if diff.geom_type == 'Polygon':
        coords = list(diff.exterior.coords)
    elif diff.geom_type == 'MultiPolygon':
        for g in diff.geoms:
            coords.extend(list(g.exterior.coords))

    coords = [(int(x), int(y)) for x, y in coords]
    return coords




def split_polygon(polygon):
    # Это чисто кастом, оставим без изменений
    n = len(polygon)
    for i in range(n):
        for j in range(i+1, n):
            for k in range(j+1, n):
                for l in range(k+1, n):
                    new_polygon1 = [polygon[i], polygon[j], polygon[k], polygon[l]]
                    new_polygon2 = [polygon[m] for m in range(n) if m not in [i, j, k, l]]
                    if not (polygon[i][0] == polygon[j][0] and polygon[j][0] == polygon[k][0] or polygon[i][0] == polygon[j][0] and polygon[j][0] == polygon[l][0] or polygon[i][0] == polygon[k][0] and polygon[k][0] == polygon[l][0] or polygon[j][0] == polygon[k][0] and polygon[k][0] == polygon[l][0] or polygon[i][1] == polygon[j][1] and polygon[j][1] == polygon[k][1] or polygon[i][1] == polygon[j][1] and polygon[j][1] == polygon[l][1] or polygon[i][1] == polygon[k][1] and polygon[k][1] == polygon[l][1] or polygon[j][1] == polygon[k][1] and polygon[k][1] == polygon[l][1]):
                        if not get_intersection_points(new_polygon1, new_polygon2):
                            return new_polygon1, new_polygon2
    return None, None


def visualize_intersection(layer1, layer2):
    fig, ax = plt.subplots()
    layer1.plot(ax, color='blue', alpha=0.5)
    layer2.plot(ax, color='red', alpha=0.5)

    for polygon1 in layer1.polygons:
        for polygon2 in layer2.polygons:
            intersection_area = layer1.get_polygons_intersection(polygon1, polygon2)
            if intersection_area:
                ax.add_patch(MplPolygon(intersection_area, closed=True, fill=True, color='green', alpha=0.5))

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
                    ax.add_patch(MplPolygon(poly1, closed=True, fill=True, color='yellow', alpha=0.5))
                    ax.add_patch(MplPolygon(poly2, closed=True, fill=True, color='yellow', alpha=0.5))
                    print(poly1, poly2)
                else:
                    ax.add_patch(MplPolygon(result_polygon, closed=True, fill=True, color='yellow', alpha=0.5))
                    print(result_polygon)

    ax.set_aspect('equal')
    ax.set_xlim([-100, 5000])
    ax.set_ylim([-100, 5000])
    plt.show()
