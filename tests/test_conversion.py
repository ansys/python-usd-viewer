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
from unittest.mock import Mock, patch

from pxr import Usd
import pytest
import pyvista
import vtk

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


def test_conversion_failure_with_non_existing_vtk_file(tmp_path):
    """Test conversion failure when VTK file does not exist."""
    dummy_vtk_path = tmp_path / "dummy.vtk"

    with pytest.raises(FileNotFoundError, match="VTK file not found"):
        VTKConverter.convert_vtk_file_to_usd(str(dummy_vtk_path))


def test_convert_unstructured_grid_to_usd():
    """Test conversion from VTK UnstructuredGrid to USD."""
    # Create a simple unstructured grid (cube)
    points = vtk.vtkPoints()
    points.InsertNextPoint(0, 0, 0)
    points.InsertNextPoint(1, 0, 0)
    points.InsertNextPoint(1, 1, 0)
    points.InsertNextPoint(0, 1, 0)
    points.InsertNextPoint(0, 0, 1)
    points.InsertNextPoint(1, 0, 1)
    points.InsertNextPoint(1, 1, 1)
    points.InsertNextPoint(0, 1, 1)
    # Create a hexahedron (cube)
    hex_cell = vtk.vtkHexahedron()
    for i in range(8):
        hex_cell.GetPointIds().SetId(i, i)
    # Create unstructured grid
    ugrid = vtk.vtkUnstructuredGrid()
    ugrid.SetPoints(points)
    ugrid.InsertNextCell(hex_cell.GetCellType(), hex_cell.GetPointIds())

    stage = VTKConverter.convert_vtk_to_usd(ugrid, mesh_name="TestCube")

    assert stage is not None, "Stage creation failed"


def test_convert_other_vtk_data_types_to_usd():
    """Test conversion from other VTK data types (vtkImageData) to USD."""
    # Create a simple image data (3D grid)
    image_data = vtk.vtkImageData()
    image_data.SetDimensions(3, 3, 3)
    image_data.SetSpacing(1.0, 1.0, 1.0)
    image_data.SetOrigin(0.0, 0.0, 0.0)

    stage = VTKConverter.convert_vtk_to_usd(image_data, mesh_name="TestImageData")

    assert stage is not None, "Stage creation failed"


def test_convert_invalid_vtk_data_raises_error():
    """Test that converting invalid VTK data raises ValueError."""
    mock_data = Mock(spec=vtk.vtkDataSet)

    # This should catch the exception and raise ValueError
    with pytest.raises(ValueError, match="Unable to convert VTK data type"):
        VTKConverter.convert_vtk_to_usd(mock_data, mesh_name="Invalid")


@pytest.mark.parametrize(
    "extension,expected_reader_class",
    [
        (".vtk", vtk.vtkPolyDataReader),
        (".vtp", vtk.vtkXMLPolyDataReader),
        (".vtu", vtk.vtkXMLUnstructuredGridReader),
        (".vts", vtk.vtkXMLStructuredGridReader),
        (".obj", vtk.vtkOBJReader),
        (".ply", vtk.vtkPLYReader),
        (".stl", vtk.vtkSTLReader),
    ],
)
def test_get_vtk_reader_supported_formats(extension, expected_reader_class):
    """Test get_vtk_reader returns correct reader for supported file formats."""
    reader = VTKConverter.get_vtk_reader(Path(f"test{extension}"))

    assert isinstance(reader, expected_reader_class), (
        f"Should return {expected_reader_class.__name__} for {extension} files"
    )


def test_get_vtk_reader_unsupported_format():
    """Test get_vtk_reader raises ValueError for unsupported formats."""
    with pytest.raises(ValueError, match="Unsupported VTK file format: .xyz"):
        VTKConverter.get_vtk_reader(Path("test.xyz"))


def test_load_asset_non_existing_file(tmp_path):
    """Test load_asset returns None for non-existing files."""
    converter = VTKConverter()
    mock_stage = Mock(spec=Usd.Stage)

    result = converter.load_asset(str(tmp_path / "dummy.vtk"), mock_stage)

    assert result is None, "Should return None for non-existing files"


def test_load_asset_unsupported_format(tmp_path):
    """Test load_asset returns None for unsupported file formats."""
    converter = VTKConverter()
    mock_stage = Mock(spec=Usd.Stage)
    unsupported_file = tmp_path / "dummy.xyz"
    unsupported_file.write_text("dummy content")

    result = converter.load_asset(str(unsupported_file), mock_stage)

    assert result is None, "Should return None for unsupported formats"


def test_load_asset_with_vtk_file(sphere_vtk_path):
    """Test load_asset successfully loads a VTK file."""
    converter = VTKConverter()
    stage = Usd.Stage.CreateInMemory()

    result = converter.load_asset(str(sphere_vtk_path), stage)

    assert result == stage, "Should return the same stage object"


@patch.object(VTKConverter, "convert_vtk_file_to_usd", side_effect=ValueError("Invalid VTK format"))
def test_load_asset_with_invalid_vtk_file(mock_convert, tmp_path):
    """Test load_asset returns None when VTK file is invalid (ValueError case)."""
    converter = VTKConverter()
    stage = Usd.Stage.CreateInMemory()
    dummy_vtk = tmp_path / "dummy.vtk"
    dummy_vtk.write_text("dummy content")

    result = converter.load_asset(str(dummy_vtk), stage)

    assert result is None, "Should return None for invalid VTK files"


@patch.object(VTKConverter, "convert_vtk_file_to_usd", side_effect=RuntimeError("Unexpected error"))
def test_load_asset_with_corrupted_file(mock_convert, tmp_path):
    """Test load_asset returns None when file causes unexpected error (Exception case)."""
    converter = VTKConverter()
    stage = Usd.Stage.CreateInMemory()
    dummy_vtk = tmp_path / "dummy.vtk"
    dummy_vtk.write_text("dummy content")

    result = converter.load_asset(str(dummy_vtk), stage)

    assert result is None, "Should return None for unexpected errors during conversion"
