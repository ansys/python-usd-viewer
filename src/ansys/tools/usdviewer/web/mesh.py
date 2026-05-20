# Copyright (C) 2025 - 2026 ANSYS, Inc. and/or its affiliates.
# SPDX-License-Identifier: MIT
#
"""Mesh extraction helpers for web viewer fallback rendering."""

from __future__ import annotations

from pathlib import Path
from typing import Any


def triangulate_faces(indices: list[int], counts: list[int]) -> list[int]:
    """Convert polygon faces to triangles using fan triangulation."""
    result = []
    idx = 0
    for count in counts:
        face = indices[idx : idx + count]
        for i in range(1, count - 1):
            result.extend([face[0], face[i], face[i + 1]])
        idx += count
    return result


def _import_usd_for_mesh_extraction() -> tuple[Any, Any]:
    """Import USD modules required for mesh extraction."""
    try:
        from pxr import Usd, UsdGeom
    except ImportError as exc:
        raise RuntimeError(
            "OpenUSD Python bindings are required to extract mesh data. Run usd-setup and ensure pxr is importable."
        ) from exc

    return Usd, UsdGeom


def _open_usd_stage(path: Path, usd: Any) -> Any:
    """Open a USD stage and raise a descriptive error on failure."""
    stage = usd.Stage.Open(str(path))
    if not stage:
        raise RuntimeError(f"Failed to open USD stage: {path}")
    return stage


def _build_tri_indices(mesh: Any, point_count: int) -> list[int]:
    """Build triangulated indices from face arrays or fallback to point order."""
    indices_attr = mesh.GetFaceVertexIndicesAttr().Get()
    counts_attr = mesh.GetFaceVertexCountsAttr().Get()
    if indices_attr and counts_attr:
        return triangulate_faces(list(indices_attr), list(counts_attr))
    return list(range(point_count))


def _extract_vertex_normals(mesh: Any, point_count: int) -> list[float] | None:
    """Extract flat vertex normals when they align with points."""
    normals_attr = mesh.GetNormalsAttr().Get()
    if not normals_attr or len(normals_attr) != point_count:
        return None
    return [coord for n in normals_attr for coord in (float(n[0]), float(n[1]), float(n[2]))]


def _extract_mesh_colors(mesh: Any, point_count: int, usd_geom: Any) -> tuple[list[float] | None, list[float] | None]:
    """Extract per-vertex colors or fallback constant color from displayColor."""
    display_color_primvar = mesh.GetDisplayColorPrimvar()
    color_attr = display_color_primvar.Get() if display_color_primvar else mesh.GetDisplayColorAttr().Get()
    color_interpolation = display_color_primvar.GetInterpolation() if display_color_primvar else None

    colors = None
    color = None
    if color_attr and len(color_attr) > 0:
        if color_interpolation in {usd_geom.Tokens.vertex, usd_geom.Tokens.varying} and len(color_attr) == point_count:
            colors = [coord for c in color_attr for coord in (float(c[0]), float(c[1]), float(c[2]))]
        else:
            c = color_attr[0]
            color = [float(c[0]), float(c[1]), float(c[2])]

    return colors, color


def _extract_mesh_payload(mesh: Any, usd_geom: Any) -> dict | None:
    """Extract web-renderable mesh payload from a USD mesh prim."""
    points_attr = mesh.GetPointsAttr().Get()
    if not points_attr:
        return None

    point_count = len(points_attr)
    flat_points = [coord for pt in points_attr for coord in (float(pt[0]), float(pt[1]), float(pt[2]))]
    tri_indices = _build_tri_indices(mesh, point_count)
    flat_normals = _extract_vertex_normals(mesh, point_count)
    colors, color = _extract_mesh_colors(mesh, point_count, usd_geom)

    return {
        "positions": flat_points,
        "indices": tri_indices,
        "normals": flat_normals,
        "colors": colors,
        "color": color,
    }


def extract_meshes_from_stage_file(path: Path) -> list[dict]:
    """Extract all mesh geometry from a USD stage file for web rendering."""
    usd, usd_geom = _import_usd_for_mesh_extraction()
    stage = _open_usd_stage(path, usd)

    meshes = []
    for prim in stage.Traverse():
        if not prim.IsA(usd_geom.Mesh):
            continue
        mesh_payload = _extract_mesh_payload(usd_geom.Mesh(prim), usd_geom)
        if mesh_payload is not None:
            meshes.append(mesh_payload)

    return meshes
