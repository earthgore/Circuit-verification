#include "Clipper2\include\clipper2\clipper.h"
#include <vector>
#include <tuple>
#include <utility>
#include <cmath>
#include <set>

using namespace Clipper2Lib;

using PointD = PointD;
using PathD = PathD;

// ===== ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ =====

inline PointD toPointD(const std::pair<double, double>& p) {
    return PointD(p.first, p.second);
}

inline std::pair<double, double> toPair(const PointD& p) {
    return {p.x, p.y};
}

inline PathD toPathD(const std::vector<std::pair<double, double>>& poly) {
    PathD result;
    for (const auto& p : poly) result.push_back(toPointD(p));
    return result;
}

inline std::vector<std::pair<double, double>> fromPathD(const PathD& path) {
    std::vector<std::pair<double, double>> result;
    for (const auto& p : path) result.push_back(toPair(p));
    return result;
}

PathD rotate_path_to_left_bottom(const PathD& path) {
    if (path.empty()) return path;

    // Ищем индекс самой левой нижней точки
    size_t idx = 0;
    for (size_t i = 1; i < path.size(); ++i) {
        if ((path[i].x < path[idx].x) || 
            (std::abs(path[i].x - path[idx].x) < 1e-9 && path[i].y < path[idx].y)) {
            idx = i;
        }
    }

    // Делаем циклический сдвиг
    PathD rotated;
    rotated.insert(rotated.end(), path.begin() + idx, path.end());
    rotated.insert(rotated.end(), path.begin(), path.begin() + idx);
    return rotated;
}

// ===== ПРОВЕРКА ПЕРЕСЕЧЕНИЯ ОТРЕЗКОВ =====

std::tuple<bool, std::pair<double, double>> do_lines_intersect(
    const std::pair<double, double> &p1, const std::pair<double, double> &p2,
    const std::pair<double, double> &q1, const std::pair<double, double> &q2)
{
    double x1 = p1.first, y1 = p1.second;
    double x2 = p2.first, y2 = p2.second;
    double x3 = q1.first, y3 = q1.second;
    double x4 = q2.first, y4 = q2.second;

    double denom = (x1-x2)*(y3-y4) - (y1-y2)*(x3-x4);
    if (std::abs(denom) < 1e-10) return {false, {0.0, 0.0}}; // Параллельны

    double px = ((x1*y2 - y1*x2)*(x3 - x4) - (x1 - x2)*(x3*y4 - y3*x4)) / denom;
    double py = ((x1*y2 - y1*x2)*(y3 - y4) - (y1 - y2)*(x3*y4 - y3*x4)) / denom;

    if ((px < std::min(x1,x2)-1e-10 || px > std::max(x1,x2)+1e-10) ||
        (px < std::min(x3,x4)-1e-10 || px > std::max(x3,x4)+1e-10) ||
        (py < std::min(y1,y2)-1e-10 || py > std::max(y1,y2)+1e-10) ||
        (py < std::min(y3,y4)-1e-10 || py > std::max(y3,y4)+1e-10))
        return {false, {0.0, 0.0}};

    return {true, {px, py}};
}

// ===== ПРОВЕРКА ТОЧКИ ВНУТРИ ПОЛИГОНА =====

bool is_point_inside_polygon(const std::pair<double, double>& point,
    const std::vector<std::pair<double, double>>& polygon)
{
    return PointInPolygon(toPointD(point), toPathD(polygon)) != PointInPolygonResult::IsOutside;
}

// ===== ТОЧКИ ПЕРЕСЕЧЕНИЯ ПОЛИГОНОВ =====

std::vector<std::pair<double, double>> get_intersection_points(
    const std::vector<std::pair<double, double>>& polygon1,
    const std::vector<std::pair<double, double>>& polygon2)
{
    int n1 = polygon1.size();
    int n2 = polygon2.size();
    std::vector<std::pair<double, double>> intersections;

    for(int i = 0; i < n1; ++i)
    {
        for(int j = 0; j < n2; ++j)
        {
            auto [intersect, point] = do_lines_intersect(
                polygon1[i], polygon1[(i + 1) % n1],
                polygon2[j], polygon2[(j + 1) % n2]
            );
            if(intersect)
            {
                intersections.push_back(point);
            }
        }
    }

    return intersections;
}

// ===== ПЕРЕСЕЧЕНИЕ ПОЛИГОНАЛЬНЫХ ОБЛАСТЕЙ =====

std::vector<std::pair<double, double>> intersect_polygon(
    const std::vector<std::pair<double, double>>& polygon1,
    const std::vector<std::pair<double, double>>& polygon2)
{
    PathsD solution;
    ClipperD clipper;
    clipper.AddSubject({toPathD(polygon1)});
    clipper.AddClip({toPathD(polygon2)});
    clipper.Execute(ClipType::Intersection, FillRule::NonZero, solution);

    if (!solution.empty())
        return fromPathD(rotate_path_to_left_bottom(solution[0]));

    std::vector<std::pair<double, double>> intersections = get_intersection_points(polygon1, polygon2);
    if(!intersections.empty())
    {
        for(const auto& point : polygon1)
        {
            if(is_point_inside_polygon(point, polygon2))
            {
                intersections.push_back(point);
            }
        }

        for(const auto& point : polygon2)
        {
            if(is_point_inside_polygon(point, polygon1))
            {
                intersections.push_back(point);
            }
        }

        std::set<std::pair<double, double>> unique_points(intersections.begin(), intersections.end());
        std::vector<std::pair<double, double>> result;
        for(const auto& p : unique_points)
        {
            result.push_back(p);
        }

        return result;
    }
    return {};
}


// ===== ВЫЧИТАНИЕ ПОЛИГОНА =====

std::vector<std::pair<double, double>> subtract_polygon(
    const std::vector<std::pair<double, double>>& polygon1,
    const std::vector<std::pair<double, double>>& polygon2)
{
    PathsD solution;
    ClipperD clipper;
    clipper.AddSubject({toPathD(polygon1)});
    clipper.AddClip({toPathD(polygon2)});
    clipper.Execute(ClipType::Difference, FillRule::NonZero, solution);

    if (!solution.empty())
        return fromPathD(rotate_path_to_left_bottom(solution[0]));

    return {};
}

// ===== СПЛИТ ПОЛИГОНА (ЗАГЛУШКА) =====

std::pair<std::vector<std::pair<double, double>>, std::vector<std::pair<double, double>>> split_polygon(
    const std::vector<std::pair<double, double>>& polygon1,
    const std::vector<std::pair<double, double>>& polygon2)
{
    PathD path1 = toPathD(polygon1);
    PathD path2 = toPathD(polygon2);

    // Ищем пересечение
    PathsD intersection;
    ClipperD clipper;
    clipper.AddSubject({path1});
    clipper.AddClip({path2});
    clipper.Execute(ClipType::Intersection, FillRule::NonZero, intersection);

    // Если пересечение найдено
    if (!intersection.empty())
    {
        // Если есть пересечение, то вычитаем второй полигон из первого
        PathsD result;
        clipper.Clear();
        clipper.AddSubject({path1});
        clipper.AddClip({path2});
        clipper.Execute(ClipType::Difference, FillRule::NonZero, result);

        // Делаем результат пригодным для возвращения
        if (result.size() >= 2)
        {
            return {
                fromPathD(rotate_path_to_left_bottom(result[0])),
                fromPathD(rotate_path_to_left_bottom(result[1]))
            };
        }
    }

    // Если пересечения нет, возвращаем пустые полигоны
    return {polygon1, {}};
}
