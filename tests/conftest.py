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

"""Pytest configuration and fixtures for USD viewer tests."""

import sys
from unittest.mock import MagicMock

import pytest
import pyvista

# Mock pxr module BEFORE test collection if it's not available
# This needs to run before any test module tries to import pxr
try:
    import pxr  # noqa: F401
except ImportError:
    # Create a comprehensive mock for the pxr module and its submodules
    mock_pxr = MagicMock()

    # Mock commonly used pxr submodules
    sys.modules["pxr"] = mock_pxr
    sys.modules["pxr.Usd"] = MagicMock()
    sys.modules["pxr.UsdGeom"] = MagicMock()
    sys.modules["pxr.Gf"] = MagicMock()
    sys.modules["pxr.Sdf"] = MagicMock()
    sys.modules["pxr.Vt"] = MagicMock()

    # Set up the mock to return these submodules when accessed
    mock_pxr.Usd = sys.modules["pxr.Usd"]
    mock_pxr.UsdGeom = sys.modules["pxr.UsdGeom"]
    mock_pxr.Gf = sys.modules["pxr.Gf"]
    mock_pxr.Sdf = sys.modules["pxr.Sdf"]
    mock_pxr.Vt = sys.modules["pxr.Vt"]


@pytest.fixture(scope="session", autouse=True)
def configure_pyvista():
    """Configure PyVista for testing."""
    # Set PyVista to run in off-screen mode for CI/CD
    pyvista.OFF_SCREEN = True

    # Configure PyVista global theme for consistent test images
    pyvista.set_plot_theme("document")

    return pyvista
