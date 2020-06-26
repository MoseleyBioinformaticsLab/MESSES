#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import re
from setuptools import setup, find_packages


def readme():
    with open('README.rst') as readme_file:
        return readme_file.read()


def find_version():
    with open('mwtab/__init__.py', 'r') as fd:
        version = re.search(r'^__version__\s*=\s*[\'"]([^\'"]*)[\'"]',
                            fd.read(), re.MULTILINE).group(1)
    if not version:
        raise RuntimeError('Cannot find version information')
    return version


REQUIRES = [
    # "docopt >= 0.6.2",
    "mwtab >= 1.0.0"
]


setup(
    name='mwtab',
    version=find_version(),
    author='Christian Powell',
    author_email='christian.david.powell@gamil.com',
    description='Converter for various metabolomics file types.',
    keywords='mwtab metabolomics workbench',
    license='BSD',
    url='https://github.com/MoseleyBioinformaticsLab/messes',
    packages=find_packages(),
    platforms='any',
    long_description=readme(),
    install_requires=REQUIRES,
    classifiers=[
        'Environment :: Console',
        'Intended Audience :: Developers',
        'Intended Audience :: Science/Research',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Topic :: Scientific/Engineering :: Bio-Informatics',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ]
)
