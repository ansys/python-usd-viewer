# Copyright (C) 2025 ANSYS, Inc. and/or its affiliates.
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
"""USDViewer main module."""

import sys

import numpy as np
from pxr import Gf, Sdf, Usd, UsdUtils
from pxr.Usdviewq.stageView import StageView
from PySide6 import QtCore, QtWidgets


class Widget(QtWidgets.QWidget):
    """USD Viewer Widget to display USD stages in Qt.

    Parameters
    ----------
    stage : Usd.Stage, optional
        The USD stage to display.
    """

    def __init__(self, stage=None):
        """Initialize the USD Viewer Widget."""
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
    title : str, optional
        The title of the viewer window. Default is "Viewer".
    size : tuple[int, int], optional
        The size of the viewer window as (width, height). Default is (750, 750).
    """

    def __init__(self, title: str = "Viewer", size: tuple[int, int] = (750, 750)):
        """Initialize the USD Viewer."""
        self._app = QtWidgets.QApplication([])

        self._title = title
        self._size = size

    def plot(self, stage: Usd.Stage) -> None:
        """Plot the given USD stage in the viewer window.

        Parameters
        ----------
        stage : Usd.Stage
            The USD stage to display.

        """
        self.window = Widget(stage)
        self.window.setWindowTitle(self._title)
        self.window.resize(QtCore.QSize(*self._size))

    def show(self) -> None:
        """Show the viewer window.

        Displays the USD viewer window and starts the Qt application event loop.
        """
        self.window.show()
        self._app.exec()

    def load_usd(self, path: str) -> Usd.Stage:
        """Load a USD stage from the given file path.

        Parameters
        ----------
        path : str
            The file path to the USD file.
        """
        with Usd.StageCacheContext(UsdUtils.StageCache.Get()):
            stage = Usd.Stage.Open(path)

        if stage:
            print(f"Stage loaded: {stage.GetRootLayer().GetDisplayName()}")
        else:
            print("Failed to load stage!")
            sys.exit(1)

        # plot the stage
        self.plot(stage)


