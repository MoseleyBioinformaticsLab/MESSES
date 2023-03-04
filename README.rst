MESSES
~~~~~~

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

The process of going from your raw experimental data to submission to an online repository 
is not an easy one, but MESSES was created to make it easier. MESSES breaks up the process 
into 3 steps, extract, validate, and convert. The extraction step adds a layer of tags 
to your raw data so that it is in a form that is more interoperable and more standardized. 
The validation step ensures the data that was extracted is valid against the `Experiment Description Schema <https://moseleybioinformaticslab.github.io/messes/experiment_description_schema.html>`__, 
`Protocol Dependent Schema <https://moseleybioinformaticslab.github.io/messes/protocol_dependent_schema.html>`__, any additional JSON schema you wish to provide, and a built 
in schema specific for the format you wish to convert to. The conversion step converts the 
extracted data to the form that is accepted by the online repository. Initially getting started 
will likely be difficult, but once things are worked out the first time this process can be 
easily added to your workflows.

Although any kind of data schema can be used for extraction into JSON. Conversion 
to another format from the extracted JSON does rely on the data being in a specific 
schema. A generalized schema was developed for MESSES that should be able to comprehensivley 
describe most experimental data. This schema is described in the `Experiment Description Schema <https://moseleybioinformaticslab.github.io/messes/experiment_description_schema.html>`__ section 
of the documentation. If MESSES is used as a library it may be possible to use a 
different data schema, but the details would be left to the user.

Tagging and initial data entry are error prone due to being done by hand, so to 
help catch mistakes MESSES includes a validate command that will help make sure 
your data is in line with your project parameters and data schema.

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
   
**Note:** If ``py`` is not installed on Windows (e.g. Python was installed via the Windows store rather than from the official Python website), the installation command is the same as Linux and Mac OS X.

**Note:** If the ``messes`` console script is not found on Windows, the CLI can be used via ``python3 -m messes`` or ``py -3.10 -m messes`` or ``path\to\console\script\messes.exe``. Alternatively, the directory where the console script is located can be added to the Path environment variable. For example, the console script may be installed at:

.. parsed-literal::
   c:\\users\\<username>\\appdata\\local\\programs\\python\\python310\\Scripts\\


Quickstart
~~~~~~~~~~
It is unlikely that you will have data that is tagged and ready to be converted, so 
it is highly recommended to first read the documentation on `tagging <https://moseleybioinformaticslab.github.io/messes/tagging.html>`__ 
and the `Experiment Description Schema <https://moseleybioinformaticslab.github.io/messes/experiment_description_schema.html>`__ so 
that you can properly tag your data first.

The expected workflow is to use the "extract" command to transform your tabular data 
into JSON, then use the "validate" command to validate the JSON based on your specific 
project schema, fix errors and warnings in the original data, repeat steps 1-3 until 
there are no more errors, and then use the "convert" command to transform the validated JSON into 
your final preferred data format. The validate command can be skipped, but it is not recommended.

A basic error free run may look like:

.. code:: bash

   messes extract your_data.csv --output your_data.json
   messes validate json your_data.json --pds your_schema.json --format desired_format
   messes convert desired_format your_data.json your_format_data
   
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
