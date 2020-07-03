messes
======

.. image:: https://img.shields.io/pypi/l/mwtab.svg
   :target: https://choosealicense.com/licenses/bsd-3-clause-clear/
   :alt: License information

|


The ``messes`` package is a Python library that facilitates the conversion of raw MS and NMR experimental data into
``mwTab`` formatted data used by the `Metabolomics Workbench`_ for archival of
Mass Spectrometry (MS) and Nuclear Magnetic Resonance (NMR) experimental data.

The ``messes`` package can be used in several ways:

   * As a library for converting raw data stored in ``excel`` formatted files into ``mwTab`` formatted files.
   * As a command-line tool to convert raw data stored in ``excel`` formatted files into ``mwTab`` formatted files.


Links
~~~~~

Coming Soon!


Installation
~~~~~~~~~~~~

Coming soon!

The ``mwtab`` package runs under and Python 3.4+. Use pip_ to install.
Starting with Python 3.4, pip_ is included by default.


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

.. code:: python

   >>> import messes
   >>>
   >>> # Here we open and convert a internal MS data JSON file into mwTab formatted data
   >>> for internal_data in messes.read_files("data\\"):
   ...      mwtabfile = convert(internal_data, "MS")
   >>> # Here we save out the converted data into a mwTab file
   >>> with open("mwtab_data.txt", 'w', encoding="UTF-8") as outfile:
   ...      mwfile = next(mwtab.read_files(mwtab_json_fpath))
   ...      mwfile.write(outfile, file_format="mwtab")
   >>>


License
~~~~~~~

This package is distributed under the BSD_ `license`.


.. _Metabolomics Workbench: http://www.metabolomicsworkbench.org
.. _GitHub: https://github.com/MoseleyBioinformaticsLab/messes
.. _ReadTheDocs: http://messes.readthedocs.io
.. _PyPI: https://pypi.org/project/messes
.. _pip: https://pip.pypa.io
.. _BSD: https://choosealicense.com/licenses/bsd-3-clause-clear/
