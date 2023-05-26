# -*- coding: utf-8 -*-
"""

"""

from setuptools import Extension
from setuptools.command.build_py import build_py as _build_py
import numpy

class build_py(_build_py):
    def run(self):
        self.run_command("build_ext")
        return super().run()

    def initialize_options(self):
        super().initialize_options()
        if self.distribution.ext_modules == None:
            self.distribution.ext_modules = []

        self.distribution.ext_modules.append(
            Extension(
                "messes.extract.cythonized_tagSheet",
                sources=["src/messes/extract/cythonized_tagSheet.pyx"],
                include_dirs=[numpy.get_include()]
            )
        )

