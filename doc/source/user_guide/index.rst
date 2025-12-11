==========
User guide
==========

This section explains key concepts for implementing the Python USD Viewer in your workflow.
You can use the Python USD Viewer in your examples as well as integrate this library into
your own code.


Default usage
-------------

This example demonstrates how to load and display a USD file using the USDViewer.

.. code-block:: python

    from ansys.tools.usdviewer import USDViewer

    # Load USD file
    path = r"example_usd_file.usda"
    viewer = USDViewer(title="USD Viewer", size=(800, 800))
    viewer.load_usd(path)
    viewer.show()