# Copyright (C) 2025 - 2026 ANSYS, Inc. and/or its affiliates.
# SPDX-License-Identifier: MIT
#
"""Utilities to export USD assets and launch a simple browser viewer."""

from __future__ import annotations

import base64
from pathlib import Path

from ansys.tools.usdviewer.vtk_converter import VTKConverter

from .glb import convert_usd_to_glb
from .templates import build_viewer_html_glb

_SUPPORTED_USD_EXTENSIONS = {".usd", ".usda", ".usdc", ".usdz"}


def export_viewer_html(
    input_path: str | Path,
    output_path: str | Path | None = None,
) -> Path:
    """Generate a self-contained HTML viewer file for embedding in other pages.

    The generated HTML embeds all mesh geometry as inline JSON and requires
    only a CDN connection for Three.js.  It is designed to be embedded in
    other web pages via an ``<iframe>``:

    .. code-block:: html

        <iframe src="model_viewer.html" width="800" height="600"
                style="border:none;"></iframe>

    Parameters
    ----------
    input_path : str | Path
        Source asset path. Supported formats are ``.usd``, ``.usda``,
        ``.usdc``, and ``.usdz``.
    output_path : str | Path | None, default: ``None``
        Full path for the generated HTML file.  When ``None``, the file is
        written alongside the source asset as ``{stem}_viewer.html``.

    Returns
    -------
    Path
        Absolute path to the generated HTML file.
    """
    source_path = Path(input_path).expanduser().resolve()
    if not source_path.exists():
        raise FileNotFoundError(f"Input file not found: {source_path}")

    extension = source_path.suffix.lower()
    if extension not in _SUPPORTED_USD_EXTENSIONS:
        supported = ", ".join(sorted(_SUPPORTED_USD_EXTENSIONS))
        raise ValueError(f"Unsupported input format '{extension}'. Supported formats: {supported}.")

    if output_path is None:
        html_path = source_path.parent / f"{source_path.stem}_viewer.html"
    else:
        html_path = Path(output_path).expanduser().resolve()

    html_path.parent.mkdir(parents=True, exist_ok=True)
    _generate_viewer_html(source_path, html_path)
    return html_path


def _prepare_source_for_web(source_path: Path, export_root: Path) -> Path:
    """Prepare a source USD file for web export.

    For files that reference VTK assets via custom ``Asset`` attributes,
    convert those assets into USD mesh data before packaging.
    """
    if source_path.suffix.lower() == ".usdz":
        return source_path

    try:
        from pxr import Usd
    except ImportError as exc:
        raise RuntimeError(
            "OpenUSD Python bindings are required to prepare web export assets. "
            "Run usd-setup and ensure pxr is importable."
        ) from exc

    stage = Usd.Stage.Open(str(source_path))
    if not stage:
        raise RuntimeError(f"Failed to open USD stage: {source_path}")

    vtk_asset_paths: list[Path] = []
    vtk_asset_attrs = []
    for prim in stage.Traverse():
        attr = prim.GetAttribute("Asset")
        if not attr:
            continue
        value = attr.Get()
        asset_path = getattr(value, "path", None)
        if not asset_path:
            continue
        if Path(asset_path).suffix.lower() not in {".vtk", ".vtp", ".vtu", ".vts", ".obj", ".ply", ".stl"}:
            continue

        resolved_asset = Path(asset_path)
        if not resolved_asset.is_absolute():
            resolved_asset = (source_path.parent / resolved_asset).resolve()
        vtk_asset_paths.append(resolved_asset)
        vtk_asset_attrs.append(attr)

    if not vtk_asset_paths:
        return source_path

    converter = VTKConverter()
    for vtk_path in vtk_asset_paths:
        loaded = converter.load_asset(str(vtk_path), stage)
        if loaded is None:
            raise RuntimeError(f"Failed to load VTK asset referenced by stage: {vtk_path}")

    # Clear custom Asset links after conversion so USDZ packaging doesn't retain
    # unresolved non-USD references that web loaders cannot consume.
    for attr in vtk_asset_attrs:
        attr.Clear()

    prepared_source = export_root / f"{source_path.stem}_webprep.usda"
    stage.Export(str(prepared_source))
    return prepared_source


def _generate_viewer_html(source_path: Path, html_path: Path) -> None:
    """Prepare mesh data and write a viewer HTML file to *html_path*.

    Converts the USD asset to GLB via ``pygltflib`` for full PBR material
    support.  Intermediate files (e.g. ``_webprep.usda``) are written to
    ``html_path.parent``.
    """
    prepared_path = _prepare_source_for_web(source_path, html_path.parent)
    glb_bytes = convert_usd_to_glb(prepared_path)
    glb_b64 = base64.b64encode(glb_bytes).decode("ascii")
    html = build_viewer_html_glb(glb_b64, source_path.name)
    html_path.write_text(html, encoding="utf-8")
