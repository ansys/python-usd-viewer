# Copyright (C) 2025 - 2026 ANSYS, Inc. and/or its affiliates.
# SPDX-License-Identifier: MIT
#
"""Export a USD viewer and embed it inside a standalone webpage via iframe.

Running this script produces two files in the same directory as the source
asset:

* ``display_color_vtk_viewer.html`` – the self-contained Three.js viewer
* ``display_color_vtk_page.html``   – a demo webpage that hosts the viewer
  inside an ``<iframe>``

Open ``display_color_vtk_page.html`` in any browser to see the result.
"""

import webbrowser
from pathlib import Path

from ansys.tools.usdviewer.web.viewer import export_viewer_html


_PAGE_TEMPLATE = (Path(__file__).parent / "assets" / "page_template.html").read_text(encoding="utf-8")


if __name__ == "__main__":
    source = Path("assets/display_color_vtk.usda")
    here = Path(__file__).parent

    viewer_path = export_viewer_html(source, output_path=here / f"{source.stem}_viewer.html")
    print(f"Viewer HTML  : {viewer_path}")

    page_path = here / f"{source.stem}_page.html"
    page_path.write_text(
        _PAGE_TEMPLATE.format(
            title=f"{source.name} – USD Viewer",
            model_name=source.name,
            viewer_filename=viewer_path.name,
        ),
        encoding="utf-8",
    )
    print(f"Wrapper page : {page_path}")

    webbrowser.open(page_path.resolve().as_uri())
