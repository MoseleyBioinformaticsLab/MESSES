#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import re
from setuptools import setup, find_packages
from Cython.Build import cythonize
import numpy


def readme():
    with open('README.rst') as readme_file:
        return readme_file.read()


def find_version():
    with open('src/messes/__init__.py', 'r') as fd:
        version = re.search(r'^__version__\s*=\s*[\'"]([^\'"]*)[\'"]',
                            fd.read(), re.MULTILINE).group(1)
    if not version:
        raise RuntimeError('Cannot find version information')
    return version


REQUIRES = [
    "docopt >= 0.6.2",
    "mwtab >= 1.0.0",
    "pandas >= 0.24.2",
    "openpyxl >= 2.6.2",
    "jellyfish >= 0.9.0",
    "jsonschema >= 4.4.0",
    "numpy >= 1.22.4"
]


setup(
    name='messes',
    version=find_version(),
    author='Christian Powell',
    author_email='christian.david.powell@gamil.com',
    description='Extract, validate, and converter tabular data for deposition into repositories.',
    keywords='mwtab metabolomics workbench',
    license='BSD',
    url='https://github.com/MoseleyBioinformaticsLab/messes',
    packages=find_packages("src", exclude=['doc', 'docs', 'vignettes']),
    package_dir={'': 'src'},
    ext_modules = cythonize("src/messes/cythonized_tagSheet.pyx"),
    include_dirs=[numpy.get_include()],
    platforms='any',
    long_description=readme(),
    install_requires=REQUIRES,
    classifiers=[
        'Environment :: Console',
        'Intended Audience :: Developers',
        'Intended Audience :: Science/Research',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3.10',
        'Topic :: Scientific/Engineering :: Bio-Informatics',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ],
    entry_points={"console_scripts": ["messes = messes.__main__:main"]}
)
