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
"""Unit tests for the USD Viewer module."""

from unittest.mock import Mock, patch

from conftest import PXR_AVAILABLE, requires_openusd
from pxr import Usd, UsdGeom
import pytest

from ansys.tools.usdviewer.viewer import USDViewer, Widget


@pytest.fixture
def mock_qt_application():
    """Mock the Qt application."""
    with patch("ansys.tools.usdviewer.viewer.QtWidgets.QApplication") as mock_app:
        mock_app_instance = Mock()
        mock_app.return_value = mock_app_instance
        yield mock_app_instance


@pytest.fixture
def mock_stage_view():
    """Mock the StageView and DefaultDataModel."""
    with patch("ansys.tools.usdviewer.viewer.StageView") as mock_view:
        mock_view_instance = Mock()
        mock_view.return_value = mock_view_instance
        mock_view.DefaultDataModel = Mock
        yield mock_view


@pytest.fixture
def test_stage():
    """Create a test USD stage."""
    stage = Usd.Stage.CreateInMemory()
    UsdGeom.Xform.Define(stage, "/TestPrim")
    return stage


def test_widget_initialization(mock_stage_view):
    """Test Widget initialization without a stage."""
    # When QtWidgets is mocked, we can't patch __init__, so just skip this complex test
    if not PXR_AVAILABLE:
        pytest.skip("Widget initialization test requires real Qt (mocked Qt doesn't support __init__ patching)")

    with patch("ansys.tools.usdviewer.viewer.QtWidgets.QWidget.__init__", return_value=None):
        with patch("ansys.tools.usdviewer.viewer.QtWidgets.QVBoxLayout"):
            widget = Widget()
            assert hasattr(widget, "model")
            assert hasattr(widget, "view")


def test_widget_initialization_with_stage(mock_stage_view, test_stage):
    """Test Widget initialization with a stage."""
    # When QtWidgets is mocked, we can't patch __init__, so just skip this complex test
    if not PXR_AVAILABLE:
        pytest.skip("Widget initialization test requires real Qt (mocked Qt doesn't support __init__ patching)")

    with patch("ansys.tools.usdviewer.viewer.QtWidgets.QWidget.__init__", return_value=None):
        with patch("ansys.tools.usdviewer.viewer.QtWidgets.QVBoxLayout"):
            with patch.object(Widget, "setStage") as mock_set_stage:
                Widget(stage=test_stage)
                mock_set_stage.assert_called_once_with(test_stage)


def test_widget_set_stage(mock_stage_view, test_stage):
    """Test Widget setStage method."""
    # When QtWidgets is mocked, we can't patch __init__, so just skip this complex test
    if not PXR_AVAILABLE:
        pytest.skip("Widget initialization test requires real Qt (mocked Qt doesn't support __init__ patching)")

    with patch("ansys.tools.usdviewer.viewer.QtWidgets.QWidget.__init__", return_value=None):
        with patch("ansys.tools.usdviewer.viewer.QtWidgets.QVBoxLayout"):
            widget = Widget()
            widget.model = Mock()
            widget.setStage(test_stage)
            assert widget.model.stage == test_stage


def test_widget_close_event(mock_stage_view):
    """Test Widget closeEvent."""
    # When QtWidgets is mocked, we can't patch __init__, so just skip this complex test
    if not PXR_AVAILABLE:
        pytest.skip("Widget initialization test requires real Qt (mocked Qt doesn't support __init__ patching)")

    with patch("ansys.tools.usdviewer.viewer.QtWidgets.QWidget.__init__", return_value=None):
        with patch("ansys.tools.usdviewer.viewer.QtWidgets.QVBoxLayout"):
            widget = Widget()
            widget.view = Mock()
            widget.view.closeRenderer = Mock()

            event = Mock()
            widget.closeEvent(event)
            widget.view.closeRenderer.assert_called_once()


def test_usd_viewer_initialization(mock_qt_application):
    """Test USDViewer initialization with default parameters."""
    viewer = USDViewer()
    assert viewer._title == "Viewer"
    assert viewer._size == (750, 750)
    assert viewer._vtk_paths == []
    assert hasattr(viewer, "_asset_resolver")


def test_usd_viewer_initialization_custom_params(mock_qt_application):
    """Test USDViewer initialization with custom parameters."""
    viewer = USDViewer(title="My Viewer", size=(1024, 768))
    assert viewer._title == "My Viewer"
    assert viewer._size == (1024, 768)


@requires_openusd
def test_usd_viewer_extract_vtk_paths(mock_qt_application, test_stage):
    """Test extracting VTK paths from USD stage."""
    viewer = USDViewer()

    # Create a prim with a VTK asset attribute
    prim = test_stage.DefinePrim("/TestMesh")
    from pxr import Sdf

    attr = prim.CreateAttribute("Asset", Sdf.ValueTypeNames.Asset)

    # Create an asset value pointing to a VTK file
    asset_value = Sdf.AssetPath("path/to/mesh.vtk")
    attr.Set(asset_value)

    vtk_paths = viewer._extract_vtk_paths(test_stage)
    assert len(vtk_paths) == 1
    assert vtk_paths[0] == "path/to/mesh.vtk"


def test_usd_viewer_extract_vtk_paths_no_assets(mock_qt_application, test_stage):
    """Test extracting VTK paths when there are no assets."""
    viewer = USDViewer()
    vtk_paths = viewer._extract_vtk_paths(test_stage)
    assert len(vtk_paths) == 0


def test_usd_viewer_extract_vtk_paths_non_vtk_assets(mock_qt_application, test_stage):
    """Test extracting VTK paths with non-VTK assets."""
    viewer = USDViewer()

    # Create a prim with a non-VTK asset
    prim = test_stage.DefinePrim("/TestMesh")
    from pxr import Sdf

    attr = prim.CreateAttribute("Asset", Sdf.ValueTypeNames.Asset)

    asset_value = Sdf.AssetPath("path/to/texture.png")
    attr.Set(asset_value)

    vtk_paths = viewer._extract_vtk_paths(test_stage)
    assert len(vtk_paths) == 0


def test_usd_viewer_load_vtk_assets(mock_qt_application, test_stage):
    """Test loading VTK assets."""
    viewer = USDViewer()
    viewer._vtk_paths = ["test1.vtk", "test2.vtk"]
    viewer._asset_resolver.load_asset = Mock(return_value=test_stage)

    with patch("builtins.print"):
        viewer._load_vtk_assets(test_stage)
        assert viewer._asset_resolver.load_asset.call_count == 2


def test_usd_viewer_load_vtk_assets_failure(mock_qt_application, test_stage):
    """Test loading VTK assets with failures."""
    viewer = USDViewer()
    viewer._vtk_paths = ["test1.vtk"]
    viewer._asset_resolver.load_asset = Mock(return_value=None)

    with patch("builtins.print"):
        viewer._load_vtk_assets(test_stage)
        viewer._asset_resolver.load_asset.assert_called_once()


def test_usd_viewer_plot(mock_qt_application, mock_stage_view, test_stage):
    """Test plotting a USD stage."""
    with patch("ansys.tools.usdviewer.viewer.Widget") as mock_widget_class:
        mock_widget = Mock()
        mock_widget_class.return_value = mock_widget

        viewer = USDViewer(title="Test Viewer", size=(800, 600))
        viewer._vtk_paths = []

        viewer.plot(test_stage)

        mock_widget_class.assert_called_once_with(test_stage)
        mock_widget.setWindowTitle.assert_called_once_with("Test Viewer")
        mock_widget.resize.assert_called_once()


def test_usd_viewer_show(mock_qt_application, mock_stage_view, test_stage):
    """Test showing the viewer window."""
    with patch("ansys.tools.usdviewer.viewer.Widget") as mock_widget_class:
        mock_widget = Mock()
        mock_widget_class.return_value = mock_widget

        viewer = USDViewer()
        viewer._vtk_paths = []
        viewer.plot(test_stage)

        viewer.show()

        mock_widget.show.assert_called_once()
        viewer._app.exec.assert_called_once()


def test_usd_viewer_load_usd(mock_qt_application, mock_stage_view, tmp_path):
    """Test loading a USD file."""
    # Create a temporary USD file
    usd_file = tmp_path / "test.usda"
    stage = Usd.Stage.CreateNew(str(usd_file))
    UsdGeom.Xform.Define(stage, "/TestPrim")
    stage.Save()

    with patch("ansys.tools.usdviewer.viewer.Widget") as mock_widget_class:
        mock_widget = Mock()
        mock_widget_class.return_value = mock_widget

        viewer = USDViewer()

        with patch("builtins.print"):
            loaded_stage = viewer.load_usd(str(usd_file))

        assert loaded_stage is not None
        mock_widget_class.assert_called_once()


def test_usd_viewer_load_usd_failure(mock_qt_application):
    """Test loading an invalid USD file."""
    viewer = USDViewer()

    with patch("ansys.tools.usdviewer.viewer.Usd.Stage.Open", return_value=None):
        with patch("builtins.print"):
            with pytest.raises(SystemExit):
                viewer.load_usd("nonexistent.usda")


def test_usd_viewer_load_asset(mock_qt_application, mock_stage_view, tmp_path):
    """Test loading an asset."""
    with patch("ansys.tools.usdviewer.viewer.Widget") as mock_widget_class:
        mock_widget = Mock()
        mock_widget_class.return_value = mock_widget

        viewer = USDViewer()
        mock_stage = Mock()
        viewer._asset_resolver.load_asset_as_usd = Mock(return_value=mock_stage)

        with patch("builtins.print"):
            loaded_stage = viewer.load_asset("test.vtk")

        assert loaded_stage == mock_stage
        viewer._asset_resolver.load_asset_as_usd.assert_called_once_with("test.vtk")
        mock_widget_class.assert_called_once()


def test_usd_viewer_load_asset_failure(mock_qt_application):
    """Test loading an asset that fails."""
    viewer = USDViewer()
    viewer._asset_resolver.load_asset_as_usd = Mock(return_value=None)

    with patch("builtins.print"):
        with pytest.raises(SystemExit):
            viewer.load_asset("nonexistent.vtk")
