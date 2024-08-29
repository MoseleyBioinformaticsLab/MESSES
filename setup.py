# -*- coding: utf-8 -*-
from setuptools import Extension, setup
from Cython.Build import cythonize
import numpy

ext_modules = [
    Extension(
        "messes.extract.cythonized_tagSheet",
        sources=["src/messes/extract/cythonized_tagSheet.pyx"],
        include_dirs=[numpy.get_include()]
    )
]

setup(
      ext_modules = cythonize(ext_modules)
      )



