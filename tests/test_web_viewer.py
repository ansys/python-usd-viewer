# Copyright (C) 2025 - 2026 ANSYS, Inc. and/or its affiliates.
# SPDX-License-Identifier: MIT
#
"""Unit tests for web viewer utilities."""

from pathlib import Path
from unittest.mock import patch

import pytest

from ansys.tools.usdviewer.web.viewer import export_viewer_html


@patch("ansys.tools.usdviewer.web.viewer._prepare_source_for_web")
def test_export_viewer_html_default_output_path(mock_prepare, tmp_path):
    """Test that export_viewer_html writes the HTML alongside the input file by default."""
    usda_path = tmp_path / "scene.usda"
    usda_path.write_text("#usda 1.0", encoding="utf-8")
    mock_prepare.return_value = usda_path

    html_path = export_viewer_html(usda_path)

    assert html_path == tmp_path / "scene_viewer.html"
    assert html_path.exists()
    html = html_path.read_text(encoding="utf-8")
    assert "glbBase64" in html


@patch("ansys.tools.usdviewer.web.viewer._prepare_source_for_web")
def test_export_viewer_html_explicit_output_path(mock_prepare, tmp_path):
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


@patch("pxr.Usd.Stage.Open")
def test_prepare_source_for_web_converts_vtk_assets(mock_stage_open, tmp_path):
    """Test that VTK assets referenced by custom Asset attributes are converted."""
    from ansys.tools.usdviewer.web.viewer import _prepare_source_for_web

    input_file = tmp_path / "scene_vtk.usda"
    input_file.write_text("#usda 1.0", encoding="utf-8")
    vtk_file = tmp_path / "mesh.vtk"
    vtk_file.write_text("vtk", encoding="utf-8")

    mock_attr = type(
        "MockAttr", (), {"Get": lambda self: type("V", (), {"path": "mesh.vtk"})(), "Clear": lambda self: None}
    )()
    mock_prim = type("MockPrim", (), {"GetAttribute": lambda self, name: mock_attr if name == "Asset" else None})()

    class MockStage:
        def Traverse(self):  # noqa: N802
            return [mock_prim]

        def Export(self, path):  # noqa: N802
            Path(path).write_text("#usda 1.0", encoding="utf-8")

    mock_stage_open.return_value = MockStage()

    with patch(
        "ansys.tools.usdviewer.web.viewer.VTKConverter.load_asset", return_value=mock_stage_open.return_value
    ) as mock_load_asset:
        prepared = _prepare_source_for_web(input_file, tmp_path)

    assert prepared.name.endswith("_webprep.usda")
    assert prepared.exists()
    mock_load_asset.assert_called_once_with(str(vtk_file.resolve()), mock_stage_open.return_value)
