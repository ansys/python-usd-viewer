# Copyright (C) 2025 - 2026 ANSYS, Inc. and/or its affiliates.
# SPDX-License-Identifier: MIT
#
"""Generate and open a browser-based USD viewer page."""

import webbrowser

from ansys.tools.usdviewer.web.viewer import export_viewer_html


if __name__ == "__main__":
    html_path = export_viewer_html("assets/complex_scene/scene.usda")
    print(f"Viewer page generated at: {html_path}")
    print("Controls: left-drag orbit, right-drag pan, mouse wheel zoom.")
    webbrowser.open(html_path.resolve().as_uri())

