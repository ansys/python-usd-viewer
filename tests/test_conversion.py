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

from pxr import Gf, Usd, UsdGeom
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


def test_convert_polydata_with_rgb_colors():
    """Test conversion of VTK polydata with RGB colors to USD."""
    stage = Usd.Stage.CreateInMemory()
    # Create a simple point cloud
    points = vtk.vtkPoints()
    points.InsertNextPoint(0, 0, 0)
    points.InsertNextPoint(1, 0, 0)
    polydata = vtk.vtkPolyData()
    polydata.SetPoints(points)
    colors = vtk.vtkUnsignedCharArray()
    colors.SetNumberOfComponents(3)
    colors.SetName("Colors")
    colors.InsertNextTuple3(255, 0, 0)  # Red
    colors.InsertNextTuple3(0, 255, 0)  # Green
    colors.InsertNextTuple3(0, 0, 255)  # Blue
    polydata.GetPointData().SetScalars(colors)

    VTKConverter.convert_polydata_to_usd_mesh(polydata, stage, "ColoredTriangle")

    # Verify colors were converted and normalized
    mesh_prim = stage.GetPrimAtPath("/ColoredTriangle")
    mesh = UsdGeom.Mesh(mesh_prim)
    display_color_attr = mesh.GetDisplayColorAttr()
    usd_colors = display_color_attr.Get()
    assert len(usd_colors) == 3, "Should have 3 colors"
    assert abs(usd_colors[0][0] - 1.0) < 0.01, "Red component should be ~1.0"
    assert abs(usd_colors[1][1] - 1.0) < 0.01, "Green component should be ~1.0"
    assert abs(usd_colors[2][2] - 1.0) < 0.01, "Blue component should be ~1.0"


def test_convert_polydata_with_rgba_colors():
    """Test conversion of VTK polydata with RGBA colors to USD (alpha ignored)."""
    stage = Usd.Stage.CreateInMemory()
    # Create a simple point cloud
    points = vtk.vtkPoints()
    points.InsertNextPoint(0, 0, 0)
    points.InsertNextPoint(1, 0, 0)
    polydata = vtk.vtkPolyData()
    polydata.SetPoints(points)
    colors = vtk.vtkFloatArray()
    colors.SetNumberOfComponents(4)
    colors.SetName("Colors")
    colors.InsertNextTuple4(1.0, 0.0, 0.0, 0.5)  # Red with 50% alpha
    colors.InsertNextTuple4(0.0, 1.0, 0.0, 1.0)  # Green with full alpha
    polydata.GetPointData().SetScalars(colors)

    VTKConverter.convert_polydata_to_usd_mesh(polydata, stage, "RGBAPoints")

    # Verify colors were converted (RGB only, alpha ignored)
    mesh_prim = stage.GetPrimAtPath("/RGBAPoints")
    mesh = UsdGeom.Mesh(mesh_prim)
    display_color_attr = mesh.GetDisplayColorAttr()
    usd_colors = display_color_attr.Get()
    assert len(usd_colors) == 2, "Should have 2 colors"
    assert abs(usd_colors[0][0] - 1.0) < 0.01, "First color red component should be ~1.0"
    assert abs(usd_colors[1][1] - 1.0) < 0.01, "Second color green component should be ~1.0"


def test_convert_usd_to_vtk_with_normalized_colors():
    """Test conversion from USD to VTK with normalized colors (0-1 range)."""
    # Create USD stage with a triangle and colors in 0-1 range
    stage = Usd.Stage.CreateInMemory()
    mesh_prim = UsdGeom.Mesh.Define(stage, "/ColoredMesh")
    points = [Gf.Vec3f(0, 0, 0), Gf.Vec3f(1, 0, 0), Gf.Vec3f(0.5, 1, 0)]
    mesh_prim.CreatePointsAttr().Set(points)
    mesh_prim.CreateFaceVertexIndicesAttr().Set([0, 1, 2])
    mesh_prim.CreateFaceVertexCountsAttr().Set([3])
    colors = [Gf.Vec3f(1.0, 0.0, 0.0), Gf.Vec3f(0.0, 1.0, 0.0), Gf.Vec3f(0.0, 0.0, 1.0)]
    mesh_prim.CreateDisplayColorAttr().Set(colors)

    polydata = VTKConverter.convert_usd_to_vtk(stage, "/ColoredMesh")

    # Verify colors were converted and scaled to 0-255
    assert polydata is not None, "Polydata should be created"
    point_data = polydata.GetPointData()
    vtk_colors = point_data.GetScalars()
    assert vtk_colors is not None, "Colors should be present"
    assert vtk_colors.GetNumberOfTuples() == 3, "Should have 3 colors"
    assert vtk_colors.GetNumberOfComponents() == 3, "Should have RGB components"
    color0 = vtk_colors.GetTuple3(0)
    color1 = vtk_colors.GetTuple3(1)
    color2 = vtk_colors.GetTuple3(2)
    assert abs(color0[0] - 255) < 1, "Red component should be ~255"
    assert abs(color1[1] - 255) < 1, "Green component should be ~255"
    assert abs(color2[2] - 255) < 1, "Blue component should be ~255"


def test_convert_usd_to_vtk_with_255_colors():
    """Test conversion from USD to VTK with colors already in 0-255 range."""
    # Create USD stage with colors in 0-255 range
    stage = Usd.Stage.CreateInMemory()
    mesh_prim = UsdGeom.Mesh.Define(stage, "/ColoredMesh255")
    points = [Gf.Vec3f(0, 0, 0), Gf.Vec3f(1, 0, 0)]
    mesh_prim.CreatePointsAttr().Set(points)
    colors = [Gf.Vec3f(128.0, 64.0, 32.0), Gf.Vec3f(200.0, 150.0, 100.0)]
    mesh_prim.CreateDisplayColorAttr().Set(colors)

    polydata = VTKConverter.convert_usd_to_vtk(stage, "/ColoredMesh255")

    point_data = polydata.GetPointData()
    vtk_colors = point_data.GetScalars()
    assert vtk_colors is not None, "Colors should be present"
    color0 = vtk_colors.GetTuple3(0)
    color1 = vtk_colors.GetTuple3(1)
    assert abs(color0[0] - 128) < 1, "Red component should be ~128"
    assert abs(color0[1] - 64) < 1, "Green component should be ~64"
    assert abs(color1[0] - 200) < 1, "Red component should be ~200"
