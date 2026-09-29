User guide
==========

This section explains key concepts for using the Python USD Viewer in your workflow.
You can use the Python USD Viewer in examples or integrate this library into your code.

Default usage
-------------

This example shows how to use the Python USD Viewer to load and display a USD file:

.. code-block:: python

    from ansys.tools.usdviewer import USDViewer

    # Load USD file
    path = r"example_usd_file.usda"
    viewer = USDViewer(title="USD Viewer", size=(800, 800))
    viewer.load_usd(path)
    viewer.show()

OpenUSD auto installer
----------------------

The Python USD Viewer includes an auto installer script that simplifies the installation of OpenUSD.
This script automates downloading, building, and installing OpenUSD, making it easy to get started with the viewer.

Run the following command in your terminal to use the OpenUSD auto installer:

.. code-block:: bash

    usd-setup [--force-reinstall]

This command downloads the latest version of OpenUSD, builds it, and installs it in the current directory
under `usd_install/`.

Use the optional `--force-reinstall` flag to force a reinstall of OpenUSD if it is already installed.
