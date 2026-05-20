# Copyright (C) 2025 - 2026 ANSYS, Inc. and/or its affiliates.
# SPDX-License-Identifier: MIT
#
"""GLB conversion helpers for USD web viewer export."""

from __future__ import annotations

from pathlib import Path
import struct
from typing import Any

from .mesh import triangulate_faces


class GLBBuilder:
    """Utility for writing GLTF buffers and accessors."""

    def __init__(self, gltf: Any, pygltflib: Any):
        self.gltf = gltf
        self.pygltflib = pygltflib
        self.binary_blob = bytearray()

    def _pad4(self) -> None:
        while len(self.binary_blob) % 4:
            self.binary_blob.append(0)

    def add_buffer_view(self, data: bytes, target: int) -> int:
        """Append binary data to the shared buffer and return its buffer-view index."""
        self._pad4()
        offset = len(self.binary_blob)
        self.binary_blob.extend(data)
        buffer_view = self.pygltflib.BufferView(buffer=0, byteOffset=offset, byteLength=len(data), target=target)
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
        accessor = self.pygltflib.Accessor(
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
        self.gltf.buffers.append(self.pygltflib.Buffer(byteLength=len(self.binary_blob)))
        self.gltf.set_binary_blob(bytes(self.binary_blob))
        return bytes(self.gltf.save_to_bytes())


def _import_glb_dependencies() -> tuple[Any, Any, Any, Any]:
    """Import optional dependencies required for GLB export."""
    try:
        import pygltflib
    except ImportError as exc:
        raise ImportError("pygltflib is required for GLB export. Install it with: pip install pygltflib") from exc

    try:
        from pxr import Usd, UsdGeom, UsdShade
    except ImportError as exc:
        raise RuntimeError(
            "OpenUSD Python bindings are required to convert USD to GLB. Run usd-setup and ensure pxr is importable."
        ) from exc

    return pygltflib, Usd, UsdGeom, UsdShade


def _open_stage_for_glb(path: Path, usd: Any) -> Any:
    """Open a USD stage for GLB conversion."""
    stage = usd.Stage.Open(str(path))
    if not stage:
        raise RuntimeError(f"Failed to open USD stage: {path}")
    return stage


def _create_gltf_scene(pygltflib: Any) -> tuple[Any, Any]:
    """Create an initialized glTF document and default scene."""
    gltf = pygltflib.GLTF2()
    gltf.asset = pygltflib.Asset(version="2.0")
    scene = pygltflib.Scene(nodes=[])
    gltf.scenes.append(scene)
    gltf.scene = 0
    return gltf, scene


def _get_triangle_indices(usd_mesh: Any) -> list[int]:
    """Get triangulated face indices for a USD mesh."""
    indices_raw = usd_mesh.GetFaceVertexIndicesAttr().Get()
    counts_raw = usd_mesh.GetFaceVertexCountsAttr().Get()
    if indices_raw and counts_raw:
        return triangulate_faces(list(indices_raw), list(counts_raw))
    points = usd_mesh.GetPointsAttr().Get() or []
    return list(range(len(points)))


def _add_position_attribute(points: list[Any], builder: GLBBuilder, pygltflib: Any) -> int:
    """Write position data and return the POSITION accessor index."""
    pos_data = struct.pack(f"{len(points) * 3}f", *[c for p in points for c in (float(p[0]), float(p[1]), float(p[2]))])
    xs = [float(p[0]) for p in points]
    ys = [float(p[1]) for p in points]
    zs = [float(p[2]) for p in points]
    pos_buffer_view = builder.add_buffer_view(pos_data, pygltflib.ARRAY_BUFFER)
    return builder.add_accessor(
        pos_buffer_view,
        pygltflib.FLOAT,
        len(points),
        pygltflib.VEC3,
        min_values=[min(xs), min(ys), min(zs)],
        max_values=[max(xs), max(ys), max(zs)],
    )


def _add_index_accessor(triangle_indices: list[int], builder: GLBBuilder, pygltflib: Any) -> int:
    """Write triangle index data and return the index accessor."""
    idx_data = struct.pack(f"{len(triangle_indices)}I", *triangle_indices)
    idx_buffer_view = builder.add_buffer_view(idx_data, pygltflib.ELEMENT_ARRAY_BUFFER)
    return builder.add_accessor(idx_buffer_view, pygltflib.UNSIGNED_INT, len(triangle_indices), pygltflib.SCALAR)


def _add_normals_attribute(
    usd_mesh: Any, points: list[Any], attributes: Any, builder: GLBBuilder, pygltflib: Any
) -> None:
    """Attach NORMAL accessor when mesh normals are compatible."""
    normals = usd_mesh.GetNormalsAttr().Get()
    if not normals or len(normals) != len(points):
        return

    norm_data = struct.pack(
        f"{len(normals) * 3}f", *[c for n in normals for c in (float(n[0]), float(n[1]), float(n[2]))]
    )
    norm_buffer_view = builder.add_buffer_view(norm_data, pygltflib.ARRAY_BUFFER)
    attributes.NORMAL = builder.add_accessor(norm_buffer_view, pygltflib.FLOAT, len(normals), pygltflib.VEC3)


def _add_uv_attribute(
    prim: Any,
    points: list[Any],
    attributes: Any,
    builder: GLBBuilder,
    pygltflib: Any,
    usd_geom: Any,
) -> None:
    """Attach TEXCOORD_0 accessor when matching UV data exists."""
    st_primvar = usd_geom.PrimvarsAPI(prim).GetPrimvar("st")
    if not st_primvar or not st_primvar.IsDefined():
        return

    st_values = st_primvar.Get()
    if not st_values or len(st_values) != len(points):
        return

    uv_data = struct.pack(f"{len(st_values) * 2}f", *[c for uv in st_values for c in (float(uv[0]), float(uv[1]))])
    uv_buffer_view = builder.add_buffer_view(uv_data, pygltflib.ARRAY_BUFFER)
    attributes.TEXCOORD_0 = builder.add_accessor(uv_buffer_view, pygltflib.FLOAT, len(st_values), pygltflib.VEC2)


def _get_display_colors(usd_mesh: Any) -> tuple[Any, Any]:
    """Return display colors and interpolation token from USD mesh."""
    display_color_primvar = usd_mesh.GetDisplayColorPrimvar()
    colors = display_color_primvar.Get() if display_color_primvar else usd_mesh.GetDisplayColorAttr().Get()
    interpolation = display_color_primvar.GetInterpolation() if display_color_primvar else None
    return colors, interpolation


def _add_display_color_attribute(
    points: list[Any],
    display_colors: Any,
    color_interpolation: Any,
    attributes: Any,
    builder: GLBBuilder,
    pygltflib: Any,
    usd_geom: Any,
) -> None:
    """Attach COLOR_0 when displayColor is vertex-compatible."""
    if not (
        display_colors
        and color_interpolation in {usd_geom.Tokens.vertex, usd_geom.Tokens.varying}
        and len(display_colors) == len(points)
    ):
        return

    color_data = struct.pack(
        f"{len(display_colors) * 3}f",
        *[c for color in display_colors for c in (float(color[0]), float(color[1]), float(color[2]))],
    )
    color_buffer_view = builder.add_buffer_view(color_data, pygltflib.ARRAY_BUFFER)
    attributes.COLOR_0 = builder.add_accessor(color_buffer_view, pygltflib.FLOAT, len(display_colors), pygltflib.VEC3)


def _append_material_and_get_index(gltf: Any, material: Any) -> int:
    """Append a GLTF material and return its index."""
    gltf.materials.append(material)
    return len(gltf.materials) - 1


def _build_material_from_shader(shader: Any, prim_name: str, pygltflib: Any) -> Any:
    """Build a GLTF material from a UsdPreviewSurface shader."""
    pbr = pygltflib.PbrMetallicRoughness()

    diffuse = shader.GetInput("diffuseColor")
    if diffuse and diffuse.Get() is not None:
        dc = diffuse.Get()
        pbr.baseColorFactor = [float(dc[0]), float(dc[1]), float(dc[2]), 1.0]

    metallic = shader.GetInput("metallic")
    if metallic and metallic.Get() is not None:
        pbr.metallicFactor = float(metallic.Get())

    roughness = shader.GetInput("roughness")
    if roughness and roughness.Get() is not None:
        pbr.roughnessFactor = float(roughness.Get())

    mat = pygltflib.Material(pbrMetallicRoughness=pbr, name=prim_name)

    emissive = shader.GetInput("emissiveColor")
    if emissive and emissive.Get() is not None:
        ec = emissive.Get()
        mat.emissiveFactor = [float(ec[0]), float(ec[1]), float(ec[2])]

    return mat


def _build_display_color_material(display_colors: Any, prim_name: str, pygltflib: Any) -> Any:
    """Build a fallback GLTF material from the first displayColor value."""
    c = display_colors[0]
    pbr = pygltflib.PbrMetallicRoughness(baseColorFactor=[float(c[0]), float(c[1]), float(c[2]), 1.0])
    return pygltflib.Material(pbrMetallicRoughness=pbr, name=f"{prim_name}_displayColor")


def _get_material_index(prim: Any, display_colors: Any, gltf: Any, pygltflib: Any, usd_shade: Any) -> int | None:
    """Resolve GLTF material index from USD bindings or displayColor fallback."""
    mat_index = None
    binding = usd_shade.MaterialBindingAPI(prim).GetDirectBinding()
    if not binding:
        return mat_index

    material = binding.GetMaterial()
    if material:
        surface_source = material.ComputeSurfaceSource()
        shader = surface_source[0] if surface_source else None
        if shader and shader.GetPrim().IsValid():
            mat = _build_material_from_shader(shader, prim.GetName(), pygltflib)
            mat_index = _append_material_and_get_index(gltf, mat)

        if mat_index is None and display_colors and len(display_colors) > 0:
            mat = _build_display_color_material(display_colors, prim.GetName(), pygltflib)
            mat_index = _append_material_and_get_index(gltf, mat)

    return mat_index


def _append_mesh_to_scene(
    prim: Any, attributes: Any, idx_acc: int, mat_index: int | None, gltf: Any, scene: Any, pygltflib: Any
) -> None:
    """Append one mesh primitive and its node to the active scene."""
    primitive = pygltflib.Primitive(attributes=attributes, indices=idx_acc, material=mat_index)
    gltf_mesh = pygltflib.Mesh(primitives=[primitive], name=prim.GetName())
    gltf.meshes.append(gltf_mesh)

    node = pygltflib.Node(mesh=len(gltf.meshes) - 1, name=prim.GetName())
    gltf.nodes.append(node)
    scene.nodes.append(len(gltf.nodes) - 1)


def _iter_usd_mesh_prims(stage: Any, usd_geom: Any) -> list[Any]:
    """Collect mesh prims from a USD stage."""
    mesh_prims = []
    for prim in stage.Traverse():
        if prim.IsA(usd_geom.Mesh):
            mesh_prims.append(prim)
    return mesh_prims


def _build_attributes_for_mesh(
    prim: Any,
    usd_mesh: Any,
    points: list[Any],
    builder: GLBBuilder,
    pygltflib: Any,
    usd_geom: Any,
) -> tuple[Any, int, Any]:
    """Build geometric attributes and index accessor for one mesh."""
    tri_indices = _get_triangle_indices(usd_mesh)
    pos_acc = _add_position_attribute(points, builder, pygltflib)
    idx_acc = _add_index_accessor(tri_indices, builder, pygltflib)

    attributes = pygltflib.Attributes(POSITION=pos_acc)
    _add_normals_attribute(usd_mesh, points, attributes, builder, pygltflib)
    _add_uv_attribute(prim, points, attributes, builder, pygltflib, usd_geom)

    display_colors, color_interpolation = _get_display_colors(usd_mesh)
    _add_display_color_attribute(
        points,
        display_colors,
        color_interpolation,
        attributes,
        builder,
        pygltflib,
        usd_geom,
    )
    return attributes, idx_acc, display_colors


def _convert_mesh_prim_to_gltf(
    prim: Any,
    gltf: Any,
    scene: Any,
    builder: GLBBuilder,
    pygltflib: Any,
    usd_geom: Any,
    usd_shade: Any,
) -> None:
    """Convert one USD mesh prim into GLTF mesh/node entries."""
    usd_mesh = usd_geom.Mesh(prim)
    points = usd_mesh.GetPointsAttr().Get()
    if not points:
        return

    attributes, idx_acc, display_colors = _build_attributes_for_mesh(
        prim,
        usd_mesh,
        points,
        builder,
        pygltflib,
        usd_geom,
    )
    mat_index = _get_material_index(prim, display_colors, gltf, pygltflib, usd_shade)
    _append_mesh_to_scene(prim, attributes, idx_acc, mat_index, gltf, scene, pygltflib)


def convert_usd_to_glb(path: Path) -> bytes:
    """Convert a USD stage to a self-contained GLB binary."""
    pygltflib, usd, usd_geom, usd_shade = _import_glb_dependencies()
    stage = _open_stage_for_glb(path, usd)
    gltf, scene = _create_gltf_scene(pygltflib)
    builder = GLBBuilder(gltf, pygltflib)

    for prim in _iter_usd_mesh_prims(stage, usd_geom):
        _convert_mesh_prim_to_gltf(prim, gltf, scene, builder, pygltflib, usd_geom, usd_shade)

    return builder.finalize()
