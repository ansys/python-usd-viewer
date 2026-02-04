===============
Getting Started
===============

This section describes how to install the Python USD viewer and quickly begin using it.

Prerequisites
-------------

A C++ compiler is required to build USD from source. Please ensure you have one of the following installed:
- Windows: visual Studio
- Linux: gcc

Installation
------------

This section guides you through installing the Python USD viewer in user mode step-by-step.

1. Create a Python virtual environment:

.. code-block:: bash

    python -m venv .venv

2. Activate the environment.

In Linux:

.. code-block:: bash

    source .venv/bin/activate

In Windows:

.. code-block:: bash

    .venv/Scripts/activate

3. Install the project:

.. code-block:: bash

    pip install .


4. Run the installation program to set up OpenUSD.

.. code-block:: bash

    usd-setup

After completing these steps, you should have the Python USD viewer installed and ready to use.