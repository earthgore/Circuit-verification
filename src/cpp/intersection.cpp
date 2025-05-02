#include <iostream>
#include <tuple>
#include <algorithm>
#include <vector>
#include <utility>
#include <set>
#include <cmath>


// Функция для вычисления ориентации
int orientation(const std::tuple<double, double> &p, const std::tuple<double, double> &q, const std::tuple<double, double> &r)
{
    double val = (std::get<1>(q) - std::get<1>(p)) * (std::get<0>(r) - std::get<0>(q)) -
              (std::get<0>(q) - std::get<0>(p)) * (std::get<1>(r) - std::get<1>(q));
    const double EPS = 1e-9;
    if(std::abs(val) < EPS)
    {
        return 0; // Коллинеарны
    }
    return (val > 0) ? 1 : 2;
}

// Функция для вычисления коэффициентов прямой
std::tuple<double, double, double> line_coefficients(const std::pair<double, double> &p1, const std::pair<double, double> &p2)
{
    double A = p2.second - p1.second;
    double B = p1.first - p2.first;
    double C = A * p1.first + B * p1.second;
    return std::make_tuple(A, B, C);
}


bool on_segment(const std::pair<double, double> &p, const std::pair<double, double> &q, const std::pair<double, double> &r)
{
    return q.first <= std::max(p.first, r.first) &&
           q.first >= std::min(p.first, r.first) &&
           q.second <= std::max(p.second, r.second) &&
           q.second >= std::min(p.second, r.second);
}


std::tuple<bool, std::pair<double, double>> do_lines_intersect(const std::pair<double, double> &p1, const std::pair<double, double> &p2,
                                                               const std::pair<double, double> &q1, const std::pair<double, double> &q2)
{
    int o1 = orientation(p1, p2, q1);
    int o2 = orientation(p1, p2, q2);
    int o3 = orientation(q1, q2, p1);
    int o4 = orientation(q1, q2, p2);

    if(o1 != o2 && o3 != o4)
    {
        auto [A1, B1, C1] = line_coefficients(p1, p2);
        auto [A2, B2, C2] = line_coefficients(q1, q2);

        double determinant = A1 * B2 - A2 * B1;
        const double EPS = 1e-9;

        if (std::abs(determinant) < EPS)
            return std::make_tuple(false, std::make_pair(0.0, 0.0));

        double x = (B2 * C1 - B1 * C2) / determinant;
        double y = (A1 * C2 - A2 * C1) / determinant;
        return std::make_tuple(true, std::make_pair(x, y));
    }

    if (o1 == 0 && on_segment(p1, q1, p2))
        return std::make_tuple(true, q1);
    if (o2 == 0 && on_segment(p1, q2, p2))
        return std::make_tuple(true, q2);
    if (o3 == 0 && on_segment(q1, p1, q2))
        return std::make_tuple(true, p1);
    if (o4 == 0 && on_segment(q1, p2, q2))
        return std::make_tuple(true, p2);

    return std::make_tuple(false, std::make_pair(0.0, 0.0));
}


bool is_point_inside_polygon(const std::pair<double, double>& point,
                              const std::vector<std::pair<double, double>>& polygon) 
{
    double x = point.first, y = point.second;
    size_t n = polygon.size();
    bool inside = false;

    if (n < 3) return false;

    auto p1 = polygon[0];

    for (int i = 0; i <= n; ++i) {
        auto p2 = polygon[i % n];

        if ((p1.first == p2.first && p1.first == x && y >= std::min(p1.second, p2.second) && y <= std::max(p1.second, p2.second)) ||
            (p1.second == p2.second && p1.second == y && x >= std::min(p1.first, p2.first) && x <= std::max(p1.first, p2.first)) ||
            ((x - p1.first) * (p2.second - p1.second) == (y - p1.second) * (p2.first - p1.first) &&
             x >= std::min(p1.first, p2.first) && x <= std::max(p1.first, p2.first) &&
             y >= std::min(p1.second, p2.second) && y <= std::max(p1.second, p2.second))) {
            return false;
        }

        if (y > std::min(p1.second, p2.second)) {
            if (y <= std::max(p1.second, p2.second)) {
                if (x <= std::max(p1.first, p2.first)) {
                    double xinters = 0;
                    if (p1.second != p2.second) {
                        xinters = (y - p1.second) * (p2.first - p1.first) / (p2.second - p1.second) + p1.first;
                    }
                    if (p1.first == p2.first || x <= xinters) {
                        inside = !inside;
                    }
                }
            }
        }

        p1 = p2;
    }

    return inside;
}

std::vector<std::pair<double, double>> sort_points_in_polygon(std::vector<std::pair<double, double>> polygon)
{
    if(polygon.empty()) return polygon;

    double center_x = 0, center_y = 0;
    for(const auto& p : polygon)
    {
        center_x += p.first;
        center_y += p.second;
    }
    center_x /= polygon.size();
    center_y /= polygon.size();

    std::sort(polygon.begin(), polygon.end(), [center_x, center_y](const std::pair<double, double>& a, const std::pair<double, double>& b)
    {
        return std::atan2(a.second - center_y, a.first - center_x) < std::atan2(b.second - center_y, b.first - center_x);
    });

    return polygon;
}


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


std::vector<std::pair<double, double>> intersect_polygon(
    const std::vector<std::pair<double, double>>& polygon1,
    const std::vector<std::pair<double, double>>& polygon2)
{
    std::vector<std::pair<double, double>> intersections = get_intersection_points(polygon1, polygon2);

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

    if(intersections.empty()) return {};

    std::set<std::pair<double, double>> unique_points(intersections.begin(), intersections.end());
    std::vector<std::pair<double, double>> result;
    for(const auto& p : unique_points)
    {
        result.push_back(p);
    }

    return sort_points_in_polygon(result);
}


std::vector<std::pair<double, double>> subtract_polygon(
    const std::vector<std::pair<double, double>>& polygon1,
    const std::vector<std::pair<double, double>>& polygon2)
{
    std::vector<std::pair<double, double>> intersections = intersect_polygon(polygon1, polygon2);

    if(intersections.empty()) return polygon1;

    std::vector<std::pair<double, double>> result;
    for(const auto& point : polygon1)
    {
        if(!is_point_inside_polygon(point, polygon2))
        {
            result.push_back(point);
        }
    }
    for(const auto& point : intersections)
    {
        if(!is_point_inside_polygon(point, polygon2))
        {
            result.push_back(point);
        }
    }

    std::set<std::pair<double, double>> unique_points(result.begin(), result.end());
    std::vector<std::pair<double, double>> final_result;
    for(const auto& p : unique_points)
    {
        final_result.push_back(p);
    }

    return sort_points_in_polygon(final_result);
}

std::pair<std::vector<std::pair<double, double>>, std::vector<std::pair<double, double>>> split_polygon(
    const std::vector<std::pair<double, double>>& polygon1, 
    const std::vector<std::pair<double, double>>& polygon2)
{
    std::vector<std::pair<double, double>> polygon = subtract_polygon(polygon1, polygon2);
    int n = polygon.size();
    for(int i = 0; i < n; ++i)
    {
        for(int j = i + 1; j < n; ++j)
        {
            for(int k = j + 1; k < n; ++k)
            {
                for(int l = k + 1; l < n; ++l)
                {
                    std::vector<std::pair<double, double>> p1 = {polygon[i], polygon[j], polygon[k], polygon[l]};
                    std::vector<std::pair<double, double>> p2;
                    for(int m = 0; m < n; ++m)
                    {
                        if(m != i && m != j && m != k && m != l)
                        {
                            p2.push_back(polygon[m]);
                        }
                    }

                    bool bad_x = (polygon[i].first == polygon[j].first && polygon[j].first == polygon[k].first) ||
                                 (polygon[i].first == polygon[j].first && polygon[j].first == polygon[l].first) ||
                                 (polygon[i].first == polygon[k].first && polygon[k].first == polygon[l].first) ||
                                 (polygon[j].first == polygon[k].first && polygon[k].first == polygon[l].first);

                    bool bad_y = (polygon[i].second == polygon[j].second && polygon[j].second == polygon[k].second) ||
                                 (polygon[i].second == polygon[j].second && polygon[j].second == polygon[l].second) ||
                                 (polygon[i].second == polygon[k].second && polygon[k].second == polygon[l].second) ||
                                 (polygon[j].second == polygon[k].second && polygon[k].second == polygon[l].second);

                    if(!bad_x && !bad_y && get_intersection_points(p1, p2).empty())
                    {
                        return {sort_points_in_polygon(p1), sort_points_in_polygon(p2)};
                    }
                }
            }
        }
    }

    return {{}, {}};
}

