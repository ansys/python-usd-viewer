Getting started
===============

This section describes how to install the Python USD Viewer in user mode and quickly begin using it.

Prerequisites
-------------

You need a C++ compiler to build USD from source. Make sure you have one of the following installed:

- Linux: GCC
- Windows: Visual Studio

Installation
------------

Follow these steps to install the Python USD Viewer in user mode:

#. Create a Python virtual environment:

.. code-block:: bash

    python -m venv .venv

#. Activate the environment:

   On Linux:

   .. code-block:: bash

       source .venv/bin/activate

   On Windows:

   .. code-block:: bash

       .venv/Scripts/activate

#. Install the project:

.. code-block:: bash

    pip install .

#. Run the setup program to configure OpenUSD:

.. code-block:: bash

    usd-setup

After completing these steps, the Python USD Viewer is installed and ready to use.