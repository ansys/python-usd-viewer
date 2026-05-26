# Copyright (C) 2025 - 2026 ANSYS, Inc. and/or its affiliates.
# SPDX-License-Identifier: MIT
#
"""Unit tests for web viewer utilities."""

from unittest.mock import patch

import pytest

from ansys.tools.usdviewer.web.html_export import export_viewer_html


@patch("ansys.tools.usdviewer.web.html_export._prepare_source_for_web")
def test_export_viewer_html_output_path(mock_prepare, tmp_path):
    """Test that export_viewer_html respects an explicit output path."""
    usda_path = tmp_path / "scene.usda"
    usda_path.write_text("#usda 1.0", encoding="utf-8")
    out_path = tmp_path / "output" / "custom.html"
    mock_prepare.return_value = usda_path

    html_path = export_viewer_html(usda_path, output_path=out_path)

    assert html_path == out_path
    assert html_path.exists()


def test_export_viewer_html_missing_file_raises(tmp_path):
    """Test that a missing input raises FileNotFoundError."""
    with pytest.raises(FileNotFoundError):
        export_viewer_html(tmp_path / "missing.usda")


def test_export_viewer_html_unsupported_extension_raises(tmp_path):
    """Test that unsupported file formats are rejected."""
    invalid_file = tmp_path / "model.obj"
    invalid_file.write_text("data", encoding="utf-8")

    with pytest.raises(ValueError, match="Unsupported input format"):
        export_viewer_html(invalid_file)
