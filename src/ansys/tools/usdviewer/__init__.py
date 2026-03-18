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
"""USD Viewer main module."""

import importlib.metadata as importlib_metadata
import os

__version__ = importlib_metadata.version(__name__.replace(".", "-"))

# When True, the viewer window is not shown. Useful for CI/CD, testing, and doc generation.
# Can be set programmatically or via the USD_VIEWER_OFF_SCREEN environment variable.
OFF_SCREEN: bool = os.environ.get("USD_VIEWER_OFF_SCREEN", "false").lower() == "true"

# When True, indicates the viewer is being used to build a Sphinx gallery.
# Implies off-screen rendering. Can be set via the USD_VIEWER_BUILDING_GALLERY env variable.
BUILDING_GALLERY: bool = os.environ.get("USD_VIEWER_BUILDING_GALLERY", "false").lower() == "true"
