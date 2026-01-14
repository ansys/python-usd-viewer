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
"""Module for conversion testing."""

from pathlib import Path

from pxr import Usd
import pytest
import pyvista

from ansys.tools.usdviewer.vtk_converter import VTKConverter


@pytest.fixture
def sphere_vtk_path():
    """Fixture to provide the path to the test sphere VTK file."""
    return Path(__file__).parent / "sphere.vtk"


def test_conversion(tmp_path, sphere_vtk_path, verify_image_cache):
    """Test conversion from VTK to USD and back to VTK.

    Parameters
    ----------
    tmp_path : Path
        Pytest fixture for temporary directory.
        Pytest fixture for temporary directory.
    sphere_vtk_path : Path
        Path to the test sphere VTK file.
    """
    # Create temporary USD file path
    usd_file = tmp_path / "sphere.usda"

    # Create a new USD stage in the temporary directory
    stage = Usd.Stage.CreateNew(str(usd_file))

    # Convert VTK to USD and add to stage
    stage = VTKConverter.convert_vtk_file_to_usd(str(sphere_vtk_path), stage)

    # Save the stage
    stage.Save()

    # Convert USD back to VTK
    vtk_pd = VTKConverter.convert_usd_to_vtk(stage)

    # Verify the conversion worked
    assert vtk_pd is not None, "VTK polydata conversion failed"

    # Visualize the converted VTK data using PyVista (off-screen for testing)
    plotter = pyvista.Plotter()
    plotter.add_mesh(vtk_pd, color="lightblue", show_edges=True)
    plotter.show()
