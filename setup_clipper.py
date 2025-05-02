from setuptools import setup, Extension
import pybind11

ext_modules = [
    Extension(
        "intersection_clipper_cpp",
        ["bindings/intersection_clipper_bind.cpp", 
         "src/cpp/intersection_clipper.cpp",
         "src/cpp/Clipper2/src/clipper.rectclip.cpp",
         "src/cpp/Clipper2/src/clipper.engine.cpp",
         "src/cpp/Clipper2/src/clipper.offset.cpp"
         ],
        include_dirs=[pybind11.get_include(), 
                    "src/cpp/Clipper2/include"   # тут лежит clipper2/clipper.h
        ],
        language="c++",
        extra_compile_args=['/std:c++17']
    )
]

setup(
    name="intersection_clipper_cpp",
    ext_modules=ext_modules,
)
