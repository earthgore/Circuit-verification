#include <iostream>
#include <tuple>
#include <algorithm>
#include <vector>
#include <utility>


// Функция для вычисления ориентации
int orientation(const std::tuple<double, double> &p, const std::tuple<double, double> &q, const std::tuple<double, double> &r)
{
    double val = (std::get<1>(q) - std::get<1>(p)) * (std::get<0>(r) - std::get<0>(q)) -
              (std::get<0>(q) - std::get<0>(p)) * (std::get<1>(r) - std::get<1>(q));
    const double EPS = 1e-9;
    if (std::abs(val) < EPS)
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

    if (o1 != o2 && o3 != o4)
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



