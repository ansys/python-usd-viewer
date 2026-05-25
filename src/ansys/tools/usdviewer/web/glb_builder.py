# Copyright (C) 2025 - 2026 ANSYS, Inc. and/or its affiliates.
# SPDX-License-Identifier: MIT
#
"""Low-level helpers to build GLB buffers and base glTF scene state."""

from __future__ import annotations

from typing import Any

import pygltflib


class GLBBuilder:
    """Utility for writing GLTF buffers and accessors."""

    def __init__(self, gltf: Any):
        """Initialize the GLBBuilder with a GLTF document."""
        self.gltf = gltf
        self.binary_blob = bytearray()

    def _pad4(self) -> None:
        while len(self.binary_blob) % 4:
            self.binary_blob.append(0)

    def add_buffer_view(self, data: bytes, target: int | None) -> int:
        """Append binary data to the shared buffer and return its buffer-view index."""
        self._pad4()
        offset = len(self.binary_blob)
        self.binary_blob.extend(data)
        buffer_view = pygltflib.BufferView(buffer=0, byteOffset=offset, byteLength=len(data))
        if target is not None:
            buffer_view.target = target
        self.gltf.bufferViews.append(buffer_view)
        return len(self.gltf.bufferViews) - 1

    def add_accessor(
        self,
        buffer_view_idx: int,
        component_type: int,
        count: int,
        accessor_type: str,
        min_values: list[float] | None = None,
        max_values: list[float] | None = None,
    ) -> int:
        """Create an accessor for an existing buffer view and return its index."""
        accessor = pygltflib.Accessor(
            bufferView=buffer_view_idx,
            byteOffset=0,
            componentType=component_type,
            count=count,
            type=accessor_type,
        )
        if min_values is not None:
            accessor.min = min_values
        if max_values is not None:
            accessor.max = max_values
        self.gltf.accessors.append(accessor)
        return len(self.gltf.accessors) - 1

    def finalize(self) -> bytes:
        """Finalize the GLTF document and return the serialized GLB bytes."""
        self.gltf.buffers.append(pygltflib.Buffer(byteLength=len(self.binary_blob)))
        self.gltf.set_binary_blob(bytes(self.binary_blob))
        data = self.gltf.save_to_bytes()
        return data if isinstance(data, bytes) else b"".join(data)


def create_gltf_scene() -> tuple[Any, Any]:
    """Create an initialized glTF document and default scene."""
    gltf = pygltflib.GLTF2()
    gltf.asset = pygltflib.Asset(version="2.0")
    scene = pygltflib.Scene(nodes=[])
    gltf.scenes.append(scene)
    gltf.scene = 0
    return gltf, scene
