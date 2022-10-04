MESSES
======

.. image:: https://img.shields.io/pypi/v/messes.svg
   :target: https://pypi.org/project/messes
   :alt: Current library version

.. image:: https://img.shields.io/pypi/pyversions/messes.svg
   :target: https://pypi.org/project/messes
   :alt: Supported Python versions

.. image:: https://github.com/MoseleyBioinformaticsLab/messes/actions/workflows/build.yml/badge.svg
   :target: https://github.com/MoseleyBioinformaticsLab/messes/actions/workflows/build.yml
   :alt: Build status

.. image:: https://codecov.io/gh/MoseleyBioinformaticsLab/messes/branch/main/graphs/badge.svg?branch=main
   :target: https://codecov.io/gh/MoseleyBioinformaticsLab/messes
   :alt: Code coverage information

.. image:: https://img.shields.io/badge/DOI-10.3390%2Fmetabo11030163-blue.svg
   :target: https://doi.org/10.3390/metabo11030163
   :alt: Citation link

.. image:: https://img.shields.io/github/stars/MoseleyBioinformaticsLab/messes.svg?style=social&label=Star
    :target: https://github.com/MoseleyBioinformaticsLab/messes
    :alt: GitHub project

|


MESSES (Metadata from Experimental SpreadSheets Extraction System) is a Python package that facilitates the conversion of tabular data into
other formats. We called it MESSES because we try to convert other people’s metadata messes into clean, well-structured, JSONized metadata. 
It was initially created to pull MS and NMR experimental data into a database, but has been generalized to work with all tabular data. The key to this 
is the `tagging <https://moseleybioinformaticslab.github.io/messes/tagging.html>`__ system. Simply add a layer of tags to any tabular data and 
MESSES can transform it into JSON and then convert it to any of the `supported formats <https://moseleybioinformaticslab.github.io/messes/supported_formats.html>`__. 

Currently Supported Formats:
    
    * mwTab
        * Used by the `Metabolomics Workbench`_.

Although any kind of table schema can be used for extraction into JSON conversion 
to another format from the extracted JSON does rely on the data being in a specific 
schema. A generalized schema was developed for MESSES that should be able to comprehensivley 
describe most experimental data. This schema is described in the `Table Schema <https://moseleybioinformaticslab.github.io/messes/table_schema.html>`__ section 
of the documentation. If MESSES is used as a library it may be possible to use a 
different table schema, but the details would be left to the user.

Tagging and initial data entry are error prone due to being done by hand, so to 
help catch mistakes MESSES includes a validate command that will help make sure 
your data is in line with your project parameters and table schema.

The MESSES package can be used in two ways:

   * As a library for converting raw data stored in Excel or CSV files into other formats.
   * As a command-line tool to convert raw data stored in Excel or CSV files into other formats.


Links
~~~~~

    * MESSES @ GitHub_
    * MESSES @ PyPI_
    * Documentation @ Pages_


Installation
~~~~~~~~~~~~

The MESSES package runs under Python 3.10+. Use pip_ to install.
Starting with Python 3.4, pip_ is included by default. Be sure to use the latest 
version of pip as older versions are known to have issues grabbing all dependencies.


Install on Linux, Mac OS X
--------------------------

.. code:: bash

   python3 -m pip install messes


Install on Windows
------------------

.. code:: bash

   py -3 -m pip install messes


Upgrade on Linux, Mac OS X
--------------------------

.. code:: bash

   python3 -m pip install messes --upgrade


Upgrade on Windows
------------------

.. code:: bash

   py -3 -m pip install messes --upgrade


Quickstart
~~~~~~~~~~
It is unlikely that you will have data that is tagged and ready to be converted, so 
it is highly recommended to first read the documentation on `tagging <https://moseleybioinformaticslab.github.io/messes/tagging.html>`__ 
and the `table schema <https://moseleybioinformaticslab.github.io/messes/table_schema.html>`__ so 
that you can properly tag your data first.

The expected workflow is to use the "extract" command to transform your tabular data 
into JSON, then use the "validate" command to validate the JSON based on your specific 
project schema, fix errors and warnings in the original data, repeat steps 1-3 until 
there are no more errors, then to use the "convert" command to transform the validated JSON into 
your final preferred data format. The validate command can be skipped, but it is not recommended.

A basic error free run may look like:

.. code:: bash

   messes extract your_data.csv --output your_data.json
   messes validate your_data.json your_schema.json
   messes convert mwtab your_data.json --to-path your_mwtab_data.txt
   
MESSES's behavior can be quite complex, so it is highly encouraged to read the 
`guide <https://moseleybioinformaticslab.github.io/messes/guide.html>`_ and `tutorial <https://moseleybioinformaticslab.github.io/messes/tutorial.html>`_.
There are also examples available in the examples folder on the GitHub_ repo.



Mac OS Note
~~~~~~~~~~~
When you try to run the program on Mac OS you may get an SSL error.

    certificate verify failed: unable to get local issuer certificate
    
This is due to a change in Mac OS and Python. To fix it go to to your Python 
folder in Applications and run the Install Certificates.command shell command 
in the /Applications/Python 3.x folder. This should fix the issue.


License
~~~~~~~

This package is distributed under the BSD `license <https://moseleybioinformaticslab.github.io/messes/license.html>`__.


.. _Metabolomics Workbench: http://www.metabolomicsworkbench.org
.. _GitHub: https://github.com/MoseleyBioinformaticsLab/messes
.. _Pages: https://moseleybioinformaticslab.github.io/messes/
.. _ReadTheDocs: http://messes.readthedocs.io
.. _PyPI: https://pypi.org/project/messes
.. _pip: https://pip.pypa.io
.. _BSD: https://choosealicense.com/licenses/bsd-3-clause-clear/
