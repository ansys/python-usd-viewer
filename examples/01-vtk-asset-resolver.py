# Copyright (C) 2025 ANSYS, Inc. and/or its affiliates.
# SPDX-License-Identifier: MIT
#

"""
.. _ref_vtk_asset_resolver_example:

===================================
VTK Asset Resolver Example
===================================

This example demonstrates how to use the asset resolver to load and display
VTK files using the USD viewer with OpenUSD asset resolution capabilities.
"""

import tempfile
from pathlib import Path

from ansys.tools.usdviewer import USDViewer, create_sample_vtk_file

# Create a temporary directory for our examples
temp_dir = Path(tempfile.mkdtemp())
print(f"Working in temporary directory: {temp_dir}")

# Create some sample VTK files for demonstration
sphere_vtk = create_sample_vtk_file(temp_dir / "sphere.vtk")
print(f"Created sample VTK file: {sphere_vtk}")

# Create a USD viewer with asset search paths
viewer = USDViewer(
    title="VTK Asset Resolver Demo",
    size=(800, 600),
    asset_search_paths=[temp_dir]  # Add our temp directory to search paths
)

# Method 1: Load VTK file directly using the generic asset loader
print("\n=== Loading VTK file as asset ===")
stage = viewer.load_asset(str(sphere_vtk))

# Show the viewer
viewer.show()
