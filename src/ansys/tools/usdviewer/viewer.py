# Copyright (C) 2025 - 2026 ANSYS, Inc. and/or its affiliates.
# SPDX-FileCopyrightText: 2019 Roy Nieterau

# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
"""USD Viewer main module."""

import sys
import warnings

try:
    from pxr import Usd, UsdUtils
    from pxr.Usdviewq.stageView import StageView
except ImportError:
    warnings.warn(
        "The 'pxr' module is required to use the USD Viewer. "
        "Install the 'usd-core' package. "
        "For installation instructions, see the documentation."
    )

try:
    from PySide6 import QtCore, QtWidgets
except ImportError:
    warnings.warn("The PySide6 module is not available in this environment. ")

from ansys.tools.usdviewer.vtk_converter import VTKConverter


class Widget(QtWidgets.QWidget):
    """USD Viewer widget to display USD stages in the Qt app.

    Parameters
    ----------
    stage : Usd.Stage, optional
        USD stage to display.
    """

    def __init__(self, stage=None):
        """Initialize the USD Viewer widget."""
        super(Widget, self).__init__()
        self.model = StageView.DefaultDataModel()

        self.view = StageView(dataModel=self.model)

        layout = QtWidgets.QVBoxLayout(self)
        layout.addWidget(self.view)
        layout.setContentsMargins(0, 0, 0, 0)

        if stage:
            self.setStage(stage)

    def setStage(self, stage):  # noqa
        """Set the USD stage to display."""
        self.model.stage = stage

    def closeEvent(self, event):  # noqa
        """Handle the close event to clean up resources."""
        # Ensure to close the renderer to avoid GlfPostPendingGLErrors
        self.view.closeRenderer()


class USDViewer:
    """USD Viewer to load and display USD files in a Qt window.

    Parameters
    ----------
    title : str, default: ``"Viewer"``
        Title of the viewer window.
    size : tuple[int, int], default: ``(750, 750)``
        Size of the viewer window in this format: ``(width, height)``.
    """

    def __init__(self, title: str = "Viewer", size: tuple[int, int] = (750, 750)):
        """Initialize the USD Viewer."""
        self._app = QtWidgets.QApplication([])

        self._title = title
        self._size = size

        # Initialize asset resolver
        self._asset_resolver = VTKConverter()
        self._vtk_paths = []

    def _load_vtk_assets(self, stage: "Usd.Stage") -> None:
        """Load VTK assets referenced in the USD stage.

        Parameters
        ----------
        stage : Usd.Stage
            USD stage to load VTK assets for.
        """
        for vtk_path in self._vtk_paths:
            print(f"Loading VTK asset: {vtk_path}")
            vtk_stage = self._asset_resolver.load_asset(vtk_path, stage)
            if vtk_stage:
                print(f"VTK asset loaded: {vtk_path}")
            else:
                print(f"Failed to load VTK asset: {vtk_path}")

    def plot(self, stage: "Usd.Stage") -> None:
        """Plot the given USD stage in the viewer window.

        Parameters
        ----------
        stage : Usd.Stage
            USD stage to display.

        """
        self._load_vtk_assets(stage)
        self.window = Widget(stage)
        self.window.setWindowTitle(self._title)
        self.window.resize(QtCore.QSize(*self._size))

    def show(self) -> None:
        """Show the USD Viewer window.

        Displays the USD Viewer window and starts the Qt app event loop.
        """
        self.window.show()
        self._app.exec()

    def _extract_vtk_paths(self, stage: "Usd.Stage") -> list[str]:
        """Extract VTK paths from a given USD stage.

        Parameters
        ----------
        stage : Usd.Stage
            USD stage to extract VTK paths from.

        Returns
        -------
        list[str]
            List of VTK paths.
        """
        vtk_paths = []
        for prim in stage.Traverse():
            attr = prim.GetAttribute("Asset")
            if attr:
                value = attr.Get()
                if value and value.path.endswith(".vtk"):
                    vtk_paths.append(value.path)
                    print(f"Found VTK asset: {value.path}")
        return vtk_paths

    def load_usd(self, path: str) -> "Usd.Stage":
        """Load a USD stage from a given file path.

        Parameters
        ----------
        path : str
            File path to the USD file.
        """
        with Usd.StageCacheContext(UsdUtils.StageCache.Get()):
            stage = Usd.Stage.Open(path)
        if stage:
            print(f"Stage loaded: {stage.GetRootLayer().GetDisplayName()}")
            self._vtk_paths = self._extract_vtk_paths(stage)
        else:
            print("Failed to load stage.")
            sys.exit(1)

        # plot the stage
        self.plot(stage)
        return stage

    def load_asset(self, asset_path: str) -> "Usd.Stage":
        """Load any supported asset (such as USD or VTK) as a USD stage.

        Parameters
        ----------
        asset_path : str
            Path to the asset file. File options include USD, VTK, OBJ, PLY, and STL.

        Returns
        -------
        Usd.Stage
            Loaded USD stage.
        """
        stage = self._asset_resolver.load_asset_as_usd(asset_path)

        if stage:
            print(f"Asset loaded: {asset_path}")
            # plot the stage
            self.plot(stage)
        else:
            print(f"Failed to load asset: {asset_path}")
            sys.exit(1)

        return stage
