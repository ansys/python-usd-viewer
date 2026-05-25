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
.. _ref_usd_web_viewer_integration:

==========================
USD Web Viewer integration
==========================

Example on how to export a USD viewer and embed it inside a standalone webpage via iframe.

Running this script produces two files in the same directory as the source
asset:

* ``display_color_vtk_viewer.html`` - the self-contained Three.js viewer
* ``display_color_vtk_page.html``   - a demo webpage that hosts the viewer
  inside an ``<iframe>``

Open ``display_color_vtk_page.html`` in any browser to see the result.
"""

import webbrowser
from pathlib import Path

from ansys.tools.usdviewer.web.html_export import export_viewer_html

# Use external template for parent HTML page to avoid cluttering the code.
_PAGE_TEMPLATE = (Path(__file__).parent / "assets" / "page_template.html").read_text(encoding="utf-8")


if __name__ == "__main__":


    source = Path("assets/display_color_vtk.usda")

    # Name of the component to be integrated.
    output_path = source.parent / f"{source.stem}_viewer.html"

    # Export the viewer HTML file for the given USD source.
    viewer_path = export_viewer_html(source, output_path=output_path)

    print(f"Viewer HTML  : {viewer_path}")

    # Generate a simple wrapper page that embeds the viewer via iframe.
    page_path = source.parent / f"{source.stem}_page.html"
    page_path.write_text(
        _PAGE_TEMPLATE.format(
            title=f"{source.name} – USD Viewer",
            model_name=source.name,
            viewer_filename=viewer_path.name,
        ),
        encoding="utf-8",
    )
    print(f"Wrapper page : {page_path}")

    # Open the wrapper page in the default web browser.
    webbrowser.open(page_path.resolve().as_uri())
