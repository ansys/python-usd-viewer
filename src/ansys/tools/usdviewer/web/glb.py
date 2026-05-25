# Copyright (C) 2025 - 2026 ANSYS, Inc. and/or its affiliates.
# SPDX-License-Identifier: MIT
#
"""GLB conversion entrypoint for USD web viewer export."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from pxr import Usd

from .glb_builder import GLBBuilder, create_gltf_scene
from .glb_lights import append_usd_lights_to_scene
from .glb_mesh import convert_mesh_prim_to_gltf, iter_usd_mesh_prims


def _open_stage_for_glb(path: Path) -> Any:
    """Open a USD stage for GLB conversion."""
    stage = Usd.Stage.Open(str(path))
    if not stage:
        raise RuntimeError(f"Failed to open USD stage: {path}")
    return stage


def convert_usd_to_glb(path: Path) -> bytes:
    """Convert a USD stage to a self-contained GLB binary.

    Parameters
    ----------
    path : Path
        Path to the USD file to convert.

    Returns
    -------
    bytes
        The GLB binary data.
    """
    stage = _open_stage_for_glb(path)
    gltf, scene = create_gltf_scene()
    builder = GLBBuilder(gltf)
    texture_cache: dict[tuple[str, str, str], int] = {}
    image_cache: dict[str, int] = {}
    sampler_cache: dict[tuple[int, int], int] = {}

    append_usd_lights_to_scene(stage, gltf, scene)

    for prim in iter_usd_mesh_prims(stage):
        convert_mesh_prim_to_gltf(
            prim,
            gltf,
            scene,
            builder,
            texture_cache,
            image_cache,
            sampler_cache,
        )

    return builder.finalize()
