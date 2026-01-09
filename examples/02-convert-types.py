# Copyright (C) 2025 - 2026 ANSYS, Inc. and/or its affiliates.
# SPDX-License-Identifier: MIT
#
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
"""
.. _ref_vtk_example:

==============================
Converting VTK to USD and back
==============================

This example shows how to convert a VTK file to USD and then back to VTK.
"""

# Import necessary modules
from ansys.tools.usdviewer.vtk_converter import VTKConverter
from ansys.tools.usdviewer.viewer import USDViewer
from pxr import Usd
import pyvista

# Read a simple VTK file
sphere = pyvista.read("sphere.vtk")

# Create a new USD stage
stage = Usd.Stage.CreateNew("sphere.usda")

# Convert VTK to USD and add to stage
stage = VTKConverter.convert_vtk_file_to_usd("sphere.vtk", stage)

# View the USD file in the USD Viewer
viewer = USDViewer(title="USD Viewer", size=(800, 800))
viewer.load_usd("sphere.usda")
viewer.show()

# Convert USD back to VTK
vtk_pd = VTKConverter.convert_usd_to_vtk(stage)

# Visualize the converted VTK data using PyVista
plotter = pyvista.Plotter()
plotter.add_mesh(vtk_pd, color="lightblue", show_edges=True)
plotter.show()