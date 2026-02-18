===============
Getting Started
===============

This section describes how to install the Python USD viewer and quickly begin using it.

Prerequisites
-------------

**Windows:**
- **Visual Studio 2022 or earlier** (Community, Professional, Enterprise, or Build Tools)
- **Visual Studio 2026 (version 18) is NOT yet supported** by OpenUSD's build system
- The `usd-setup` script relies on OpenUSD's `build_usd.py`, which currently only supports up to Visual Studio 2022 (version 17)

**Recommended installation:**
- [Visual Studio 2022 Build Tools](https://visualstudio.microsoft.com/downloads/#build-tools-for-visual-studio-2022)
- During installation, select **"Desktop development with C++"**

**Linux/macOS:**
- C++ compiler should be available by default (gcc/g++ on Linux, clang on macOS)

Other Requirements
~~~~~~~~~~~~~~~~~~

- CMake 3.14 or later.
- Git (for cloning OpenUSD repository)

Installation
------------

This section guides you through installing the Python USD viewer in user mode step-by-step.

1. Create a Python virtual environment:

.. code-block:: bash

    pip install uv
    uv venv .venv

2. Activate the environment.

In Linux:

.. code-block:: bash

    source .venv/bin/activate

In Windows:

.. code-block:: bash

    .venv/Scripts/activate

3. Install the project:

.. code-block:: bash

    uv sync


4. Run the installation program to set up OpenUSD.

.. code-block:: bash

    usd-setup

.. warning::

   This script might fail due to the script not being able to reach Visual Studio executables in Windows environments.
   If this happens, please ensure that Visual Studio executables are available in your system's PATH environment variable.
   You can do this by adding the path to the Visual Studio installation directory
   (for example, ``C:\Program Files\Microsoft Visual Studio\2022\Community\VC\Tools\MSVC\14.44\bin\Hostx64\x64``,
   ``C:\Program Files\Microsoft Visual Studio\2022\Community\Common7\IDE``,
   ``C:\Program Files\Microsoft Visual Studio\2022\Community\Common7\Tools``) to your PATH.

After completing these steps, you should have the Python USD viewer installed and ready to use.