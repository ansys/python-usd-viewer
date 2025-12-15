===============
Getting Started
===============

This section describes how to install the Python USD viewer and quickly begin using it.

Prerequisites
-------------

A C++ compiler is required to build USD from source. Please ensure you have one of the following installed:
- Windows: Visual Studio
- Linux: GCC

Installation
------------

This section guides you through installing the Python USD viewer in user mode step-by-step.

1.- Create a Python virtual environment:

.. code-block:: bash

    python -m venv .venv

2.- Activate the environment.

In Linux:

.. code-block:: bash

    source .venv/bin/activate

In Windows:

.. code-block:: bash

    .venv/Scripts/activate

3.- Install the project:

.. code-block:: bash

    pip install .

4.- Clone the OpenUSD repository.

.. code-block:: bash

    git clone https://github.com/PixarAnimationStudios/OpenUSD.git

5.- Build OpenUSD from binaries.

.. code-block:: bash

    python OpenUSD/build_scripts/build_usd.py /path/to/my_usd_install_dir


After completing these steps, you should have the Python USD viewer installed and ready to use.