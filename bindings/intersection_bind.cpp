#include <pybind11/pybind11.h>
#include <pybind11/stl.h> 
namespace py = pybind11;

std::tuple<bool, std::pair<double, double>> do_lines_intersect(const std::pair<double, double> &p1, const std::pair<double, double> &p2,
    const std::pair<double, double> &q1, const std::pair<double, double> &q2);

bool is_point_inside_polygon(const std::pair<double, double>& point,
    const std::vector<std::pair<double, double>>& polygon);

std::vector<std::pair<double, double>> get_intersection_points(
    const std::vector<std::pair<double, double>>& polygon1,
    const std::vector<std::pair<double, double>>& polygon2);

std::vector<std::pair<double, double>> intersect_polygon(
    const std::vector<std::pair<double, double>>& polygon1,
    const std::vector<std::pair<double, double>>& polygon2);

std::vector<std::pair<double, double>> subtract_polygon(
    const std::vector<std::pair<double, double>>& polygon1,
    const std::vector<std::pair<double, double>>& polygon2);

std::pair<std::vector<std::pair<double, double>>, std::vector<std::pair<double, double>>> split_polygon(
    const std::vector<std::pair<double, double>>& polygon);

PYBIND11_MODULE(intersection_cpp, m) 
{
    m.def("is_point_inside_polygon", &is_point_inside_polygon, "Check if point is inside polygon");
    m.def("do_lines_intersect", &do_lines_intersect, "Check if lines intersect");
    m.def("get_intersection_points", &get_intersection_points, "Get all intersection points between two polygons");
    m.def("intersect_polygon", &intersect_polygon, "Intersect two polygons");
    m.def("subtract_polygon", &subtract_polygon, "Subtract one polygon from another");
    m.def("split_polygon", &split_polygon, "Split a polygon into two non-overlapping parts");
}
