==========
User guide
==========

This section explains key concepts for implementing the Python USD Viewer in your workflow.
You can use the Python USD Viewer in your examples as well as integrate this library into
your own code.


Default usage
-------------

This example demonstrates how to load and display a USD file using the USD Viewer.

.. code-block:: python

    from ansys.tools.usdviewer import USDViewer

    # Load USD file
    path = r"example_usd_file.usda"
    viewer = USDViewer(title="USD Viewer", size=(800, 800))
    viewer.load_usd(path)
    viewer.show()


OpenUSD auto installer
----------------------

The USD Viewer includes an auto installer script to simplify the installation of OpenUSD.
This script automates the process of downloading, building, and installing OpenUSD, making it easier for
users to get started with the viewer.

To use the auto installer, run the following command in your terminal:

.. code-block:: bash

    usd-setup [--force-reinstall]

This command downloads the latest version of OpenUSD, builds it, and installs it in the current directory
under `usd_install/`.
The optional `--force-reinstall` flag can be used to force a reinstall of OpenUSD, if it is already installed.
