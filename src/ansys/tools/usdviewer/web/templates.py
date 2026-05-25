# Copyright (C) 2025 - 2026 ANSYS, Inc. and/or its affiliates.
# SPDX-License-Identifier: MIT
#
"""HTML template rendering helpers for web viewer export."""

from __future__ import annotations

import json
from pathlib import Path

_GLB_TEMPLATE_FILE = "glb_template.html"


def build_viewer_html_glb(glb_b64: str, model_name: str) -> str:
    """Build a self-contained HTML viewer that renders a base64-encoded GLB."""
    template = _load_template(_GLB_TEMPLATE_FILE)
    return template.replace("__MODEL_NAME_JSON__", json.dumps(model_name)).replace(
        "__GLB_B64_JSON__", json.dumps(glb_b64)
    )


def _load_template(template_name: str) -> str:
    """Load a viewer HTML template from the package directory."""
    template_path = Path(__file__).with_name(template_name)
    if not template_path.exists():
        raise RuntimeError(f"Viewer template not found: {template_path}")
    return template_path.read_text(encoding="utf-8")
