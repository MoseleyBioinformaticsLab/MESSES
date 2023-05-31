User Guide
==========

.. include:: ../README.rst

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
      * To install docopt_, run the following:

        .. code:: bash

           python3 -m pip install docopt  # On Linux, Mac OS X
           py -3 -m pip install docopt    # On Windows
           
   * jsonschema_ for validating JSON.
      * To install the jsonschema_ Python library, run the following:

        .. code:: bash

           python3 -m pip install jsonschema  # On Linux, Mac OS X
           py -3 -m pip install jsonschema    # On Windows
                     
   * pandas_ for easy data manipulation.
      * To install the pandas_ Python library, run the following:

        .. code:: bash

           python3 -m pip install pandas  # On Linux, Mac OS X
           py -3 -m pip install pandas    # On Windows
           
   * openpyxl_ for saving Excel files in pandas.
      * To install the openpyxl_ Python library, run the following:

        .. code:: bash

           python3 -m pip install openpyxl  # On Linux, Mac OS X
           py -3 -m pip install openpyxl    # On Windows
           
    * xlsxwriter_ for saving Excel files in pandas.
       * To install the xlsxwriter_ Python library, run the following:

         .. code:: bash

            python3 -m pip install xlsxwriter  # On Linux, Mac OS X
            py -3 -m pip install xlsxwriter    # On Windows
           
    * jellyfish_ for saving Excel files in pandas.
       * To install the jellyfish_ Python library, run the following:

         .. code:: bash

            python3 -m pip install jellyfish  # On Linux, Mac OS X
            py -3 -m pip install jellyfish    # On Windows
            
    * mwtab_ for saving Excel files in pandas.
       * To install the mwtab_ Python library, run the following:

         .. code:: bash

            python3 -m pip install mwtab  # On Linux, Mac OS X
            py -3 -m pip install mwtab    # On Windows
           
           

Developers
~~~~~~~~~~

Any developers that wish to contribute should do so through `GitHub Issues <https://github.com/MoseleyBioinformaticsLab/MESSES/issues>`__ 
and pull requests.






.. _virtualenv: https://virtualenv.pypa.io/
.. _docopt: https://pypi.org/project/docopt/
.. _jsonschema: https://pypi.org/project/jsonschema/
.. _pandas: https://pypi.org/project/pandas/
.. _openpyxl: https://pypi.org/project/openpyxl/
.. _xlsxwriter: https://pypi.org/project/xlsxwriter/
.. _jellyfish: https://pypi.org/project/jellyfish/
.. _mwtab: https://pypi.org/project/mwtab/