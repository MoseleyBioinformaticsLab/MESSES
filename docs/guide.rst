User Guide
==========

Description
~~~~~~~~~~~

MESSES was created to help turn tabular experimental data into a standardized 
JSON format more suitable for data deposition and public sharing. It is quite 
flexible and powerful, but does require some intellectual overhead to understand 
all of the concepts and features it provides.

Installation
~~~~~~~~~~~~

The MESSES package runs under Python 3.10+. Use pip_ to install.
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



Install inside virtualenv
-------------------------

For an isolated install, you can run the same inside a virtualenv_.

.. code:: bash

   $ virtualenv -p /usr/bin/python3 venv            # create virtual environment, use python3 interpreter

   $ source venv/bin/activate                       # activate virtual environment

   $ python3 -m pip install messes                  # install messes as usual

   $ deactivate                                     # if you are done working in the virtual environment

Get the source code
~~~~~~~~~~~~~~~~~~~

Code is available on GitHub: https://github.com/MoseleyBioinformaticsLab/messes

You can either clone the public repository:

.. code:: bash

   $ https://github.com/MoseleyBioinformaticsLab/messes.git

Or, download the tarball and/or zipball:

.. code:: bash

   $ curl -OL https://github.com/MoseleyBioinformaticsLab/messes/tarball/main

   $ curl -OL https://github.com/MoseleyBioinformaticsLab/messes/zipball/main

Once you have a copy of the source, you can embed it in your own Python package,
or install it into your system site-packages easily:

.. code:: bash

   $ python3 setup.py install

Dependencies
~~~~~~~~~~~~

The MESSES package depends on several Python libraries. The ``pip`` command
will install all dependencies automatically, but if you wish to install them manually,
run the following commands:

   * docopt_ for creating the command-line interface.
      * To install docopt_ run the following:

        .. code:: bash

           python3 -m pip install docopt  # On Linux, Mac OS X
           py -3 -m pip install docopt    # On Windows
           
   * jsonschema_ for validating JSON.
      * To install the jsonschema_ Python library run the following:

        .. code:: bash

           python3 -m pip install jsonschema  # On Linux, Mac OS X
           py -3 -m pip install jsonschema    # On Windows
                     
   * pandas_ for easy data manipulation.
      * To install the pandas_ Python library run the following:

        .. code:: bash

           python3 -m pip install pandas  # On Linux, Mac OS X
           py -3 -m pip install pandas    # On Windows
           
   * openpyxl_ for saving Excel files in pandas.
      * To install the openpyxl_ Python library run the following:

        .. code:: bash

           python3 -m pip install openpyxl  # On Linux, Mac OS X
           py -3 -m pip install openpyxl    # On Windows
           
           

Basic usage
~~~~~~~~~~~



.. code-block:: console





.. _pip: https://pip.pypa.io/
.. _virtualenv: https://virtualenv.pypa.io/
.. _docopt: https://pypi.org/project/docopt/
.. _jsonschema: https://pypi.org/project/jsonschema/
.. _pandas: https://pypi.org/project/pandas/
.. _openpyxl: https://pypi.org/project/openpyxl/