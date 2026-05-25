# Copyright (C) 2025 - 2026 ANSYS, Inc. and/or its affiliates.
# SPDX-License-Identifier: MIT
#
"""GLB conversion helpers for USD web viewer export."""

from __future__ import annotations

import mimetypes
from pathlib import Path
import struct
from typing import Any

from pxr import Usd, UsdGeom, UsdLux, UsdShade
import pygltflib


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


class GLBBuilder:
    """Utility for writing GLTF buffers and accessors.

    Abstracts the low-level glTF buffer/accessor bookkeeping when
    converting USD geometry into a .glb file for web viewing.

    Parameters
    ----------
    gltf : Any
        An instance of pygltflib.GLTF2 to populate with buffer views and accessors
    """

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


def _open_stage_for_glb(path: Path) -> Any:
    """Open a USD stage for GLB conversion."""
    stage = Usd.Stage.Open(str(path))
    if not stage:
        raise RuntimeError(f"Failed to open USD stage: {path}")
    return stage


def _create_gltf_scene() -> tuple[Any, Any]:
    """Create an initialized glTF document and default scene."""
    gltf = pygltflib.GLTF2()
    gltf.asset = pygltflib.Asset(version="2.0")
    scene = pygltflib.Scene(nodes=[])
    gltf.scenes.append(scene)
    gltf.scene = 0
    return gltf, scene


def _ensure_lights_extension(gltf: Any) -> list[dict[str, Any]]:
    """Ensure KHR_lights_punctual is declared and return its light list."""
    if gltf.extensionsUsed is None:
        gltf.extensionsUsed = []
    if "KHR_lights_punctual" not in gltf.extensionsUsed:
        gltf.extensionsUsed.append("KHR_lights_punctual")

    if gltf.extensions is None:
        gltf.extensions = {}

    lights_ext = gltf.extensions.get("KHR_lights_punctual")
    if lights_ext is None:
        lights_ext = {"lights": []}
        gltf.extensions["KHR_lights_punctual"] = lights_ext

    lights = lights_ext.get("lights")
    if lights is None:
        lights = []
        lights_ext["lights"] = lights

    return lights


def _get_light_schema_and_type(prim: Any) -> tuple[Any, str] | None:
    """Map a USD light prim to a KHR_lights_punctual-compatible type."""
    if prim.IsA(UsdLux.DistantLight):
        return UsdLux.DistantLight(prim), "directional"

    if prim.IsA(UsdLux.SphereLight):
        return UsdLux.SphereLight(prim), "point"

    if prim.IsA(UsdLux.DiskLight):
        return UsdLux.DiskLight(prim), "point"

    return None


def _make_gltf_light(prim: Any) -> dict[str, Any] | None:
    """Build one glTF punctual light description from a USD light prim."""
    schema_and_type = _get_light_schema_and_type(prim)
    if schema_and_type is None:
        return None

    light_schema, light_type = schema_and_type
    color_value = light_schema.GetColorAttr().Get()
    intensity_value = light_schema.GetIntensityAttr().Get()
    exposure_value = light_schema.GetExposureAttr().Get()

    if intensity_value is None:
        intensity_value = 1.0
    intensity = float(intensity_value)
    if exposure_value is not None:
        intensity *= 2.0 ** float(exposure_value)

    # USD light intensity conventions vary across renderers and can be orders
    # of magnitude larger than typical WebGL values.
    if light_type == "directional":
        intensity /= 50000.0
    else:
        intensity /= 500.0
    intensity = max(0.0, min(intensity, 20.0))

    if color_value is None:
        color = [1.0, 1.0, 1.0]
    else:
        color = [float(color_value[0]), float(color_value[1]), float(color_value[2])]

    light: dict[str, Any] = {
        "type": light_type,
        "color": color,
        "intensity": intensity,
        "name": prim.GetName(),
    }
    return light


def _append_usd_lights_to_scene(stage: Any, gltf: Any, scene: Any) -> None:
    """Convert supported USD lights into glTF KHR_lights_punctual lights."""
    lights = _ensure_lights_extension(gltf)

    for prim in stage.Traverse():
        gltf_light = _make_gltf_light(prim)
        if gltf_light is None:
            continue

        light_index = len(lights)
        lights.append(gltf_light)

        node = pygltflib.Node(
            name=prim.GetName(),
            extensions={"KHR_lights_punctual": {"light": light_index}},
        )

        xformable = UsdGeom.Xformable(prim)
        if xformable:
            world = xformable.ComputeLocalToWorldTransform(Usd.TimeCode.Default())
            translation = world.ExtractTranslation()
            node.translation = [float(translation[0]), float(translation[1]), float(translation[2])]

        gltf.nodes.append(node)
        scene.nodes.append(len(gltf.nodes) - 1)


def _get_triangle_indices(usd_mesh: Any) -> list[int]:
    """Get triangulated face indices for a USD mesh."""
    indices_raw = usd_mesh.GetFaceVertexIndicesAttr().Get()
    counts_raw = usd_mesh.GetFaceVertexCountsAttr().Get()
    if indices_raw and counts_raw:
        return triangulate_faces(list(indices_raw), list(counts_raw))
    points = usd_mesh.GetPointsAttr().Get() or []
    return list(range(len(points)))


def _add_position_attribute(points: list[Any], builder: GLBBuilder) -> int:
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


def _add_index_accessor(triangle_indices: list[int], builder: GLBBuilder) -> int:
    """Write triangle index data and return the index accessor."""
    idx_data = struct.pack(f"{len(triangle_indices)}I", *triangle_indices)
    idx_buffer_view = builder.add_buffer_view(idx_data, pygltflib.ELEMENT_ARRAY_BUFFER)
    return builder.add_accessor(idx_buffer_view, pygltflib.UNSIGNED_INT, len(triangle_indices), pygltflib.SCALAR)


def _add_normals_attribute(usd_mesh: Any, points: list[Any], attributes: Any, builder: GLBBuilder) -> None:
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
    attributes: Any,
    uv_values: list[tuple[float, float]] | None,
    builder: GLBBuilder,
) -> None:
    """Attach TEXCOORD_0 accessor when matching UV data exists."""
    if not uv_values:
        return

    uv_data = struct.pack(f"{len(uv_values) * 2}f", *[c for uv in uv_values for c in (float(uv[0]), float(uv[1]))])
    uv_buffer_view = builder.add_buffer_view(uv_data, pygltflib.ARRAY_BUFFER)
    attributes.TEXCOORD_0 = builder.add_accessor(uv_buffer_view, pygltflib.FLOAT, len(uv_values), pygltflib.VEC2)


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
) -> None:
    """Attach COLOR_0 when displayColor is vertex-compatible."""
    if not (
        display_colors
        and color_interpolation in {UsdGeom.Tokens.vertex, UsdGeom.Tokens.varying}
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


def _build_material_from_shader(shader: Any, prim_name: str) -> Any:
    """Build a GLTF material from a UsdPreviewSurface shader."""
    # Match UsdPreviewSurface defaults to avoid glTF defaults (metallic=1)
    # when USD scalar inputs are texture-connected and return None.
    pbr = pygltflib.PbrMetallicRoughness(
        baseColorFactor=[1.0, 1.0, 1.0, 1.0],
        metallicFactor=0.0,
        roughnessFactor=0.5,
    )

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

    mat = pygltflib.Material(pbrMetallicRoughness=pbr, name=prim_name, doubleSided=True)

    emissive = shader.GetInput("emissiveColor")
    if emissive and emissive.Get() is not None:
        ec = emissive.Get()
        mat.emissiveFactor = [float(ec[0]), float(ec[1]), float(ec[2])]

    return mat


def _get_connected_shader_input(shader: Any, input_name: str) -> tuple[Any, str] | None:
    """Return connected shader and output name for a shader input."""
    shader_input = shader.GetInput(input_name)
    if not shader_input:
        return None

    connected = shader_input.GetConnectedSource()
    if not connected:
        return None

    source_api, output_name, _ = connected
    source_prim = source_api.GetPrim()
    if not source_prim or not source_prim.IsValid():
        return None

    source_shader = UsdShade.Shader(source_prim)
    if not source_shader or not source_shader.GetPrim().IsValid():
        return None

    return source_shader, output_name


def _map_wrap_mode(token: Any) -> int:
    """Map USD wrap token to glTF sampler wrap mode."""
    if token == "repeat":
        return pygltflib.REPEAT
    if token == "mirror":
        return pygltflib.MIRRORED_REPEAT
    return pygltflib.CLAMP_TO_EDGE


def _resolve_asset_file_path(asset_input: Any, shader_prim: Any) -> Path | None:
    """Resolve a USD asset path from an input to a file path."""
    if not asset_input:
        return None

    asset_value = asset_input.Get()
    if asset_value is None:
        return None

    resolved = getattr(asset_value, "resolvedPath", None)
    if resolved:
        resolved_path = Path(str(resolved))
        if resolved_path.exists():
            return resolved_path

    authored = getattr(asset_value, "path", None)
    if not authored:
        return None

    authored_path = Path(str(authored))
    if authored_path.is_absolute() and authored_path.exists():
        return authored_path

    layer = shader_prim.GetStage().GetRootLayer()
    if not layer:
        return None
    layer_path = Path(layer.realPath)
    candidate = (layer_path.parent / authored_path).resolve()
    return candidate if candidate.exists() else None


def _get_texture_index_from_usd_uv_texture(
    source_shader: Any,
    gltf: Any,
    builder: GLBBuilder,
    texture_cache: dict[tuple[str, str, str], int],
    image_cache: dict[str, int],
    sampler_cache: dict[tuple[int, int], int],
) -> int | None:
    """Create or reuse a glTF texture index from a UsdUVTexture shader."""
    shader_id = source_shader.GetIdAttr().Get()
    if shader_id != "UsdUVTexture":
        return None

    file_path = _resolve_asset_file_path(source_shader.GetInput("file"), source_shader.GetPrim())
    if file_path is None:
        return None

    wrap_s = _map_wrap_mode(source_shader.GetInput("wrapS").Get() if source_shader.GetInput("wrapS") else None)
    wrap_t = _map_wrap_mode(source_shader.GetInput("wrapT").Get() if source_shader.GetInput("wrapT") else None)

    texture_key = (str(file_path), str(wrap_s), str(wrap_t))
    cached_texture = texture_cache.get(texture_key)
    if cached_texture is not None:
        return cached_texture

    image_key = str(file_path)
    image_index = image_cache.get(image_key)
    if image_index is None:
        image_bytes = file_path.read_bytes()
        image_buffer_view = builder.add_buffer_view(image_bytes, None)
        mime_type, _ = mimetypes.guess_type(str(file_path))
        if mime_type is None:
            mime_type = "image/png"
        gltf.images.append(pygltflib.Image(bufferView=image_buffer_view, mimeType=mime_type, name=file_path.name))
        image_index = len(gltf.images) - 1
        image_cache[image_key] = image_index

    sampler_key = (wrap_s, wrap_t)
    sampler_index = sampler_cache.get(sampler_key)
    if sampler_index is None:
        gltf.samplers.append(pygltflib.Sampler(wrapS=wrap_s, wrapT=wrap_t))
        sampler_index = len(gltf.samplers) - 1
        sampler_cache[sampler_key] = sampler_index

    gltf.textures.append(pygltflib.Texture(source=image_index, sampler=sampler_index))
    texture_index = len(gltf.textures) - 1
    texture_cache[texture_key] = texture_index
    return texture_index


def _apply_preview_surface_textures(
    shader: Any,
    material: Any,
    gltf: Any,
    builder: GLBBuilder,
    texture_cache: dict[tuple[str, str, str], int],
    image_cache: dict[str, int],
    sampler_cache: dict[tuple[int, int], int],
) -> None:
    """Apply supported UsdPreviewSurface texture connections to a GLTF material."""
    pbr = material.pbrMetallicRoughness

    diffuse_connection = _get_connected_shader_input(shader, "diffuseColor")
    if diffuse_connection is not None:
        diffuse_shader, _ = diffuse_connection
        tex_index = _get_texture_index_from_usd_uv_texture(
            diffuse_shader,
            gltf,
            builder,
            texture_cache,
            image_cache,
            sampler_cache,
        )
        if tex_index is not None:
            pbr.baseColorTexture = pygltflib.TextureInfo(index=tex_index)

    normal_connection = _get_connected_shader_input(shader, "normal")
    if normal_connection is not None:
        normal_shader, _ = normal_connection
        tex_index = _get_texture_index_from_usd_uv_texture(
            normal_shader,
            gltf,
            builder,
            texture_cache,
            image_cache,
            sampler_cache,
        )
        if tex_index is not None:
            material.normalTexture = pygltflib.NormalMaterialTexture(index=tex_index)

    emissive_connection = _get_connected_shader_input(shader, "emissiveColor")
    if emissive_connection is not None:
        emissive_shader, _ = emissive_connection
        tex_index = _get_texture_index_from_usd_uv_texture(
            emissive_shader,
            gltf,
            builder,
            texture_cache,
            image_cache,
            sampler_cache,
        )
        if tex_index is not None:
            material.emissiveTexture = pygltflib.TextureInfo(index=tex_index)

    opacity_input = shader.GetInput("opacity")
    opacity_threshold_input = shader.GetInput("opacityThreshold")
    opacity_threshold = float(opacity_threshold_input.Get()) if opacity_threshold_input else 0.0
    has_connected_opacity = _get_connected_shader_input(shader, "opacity") is not None
    opacity_value = float(opacity_input.Get()) if opacity_input and opacity_input.Get() is not None else 1.0

    if has_connected_opacity or opacity_value < 1.0:
        material.alphaMode = "MASK" if opacity_threshold > 0.0 else "BLEND"
        if opacity_threshold > 0.0:
            material.alphaCutoff = opacity_threshold


def _build_display_color_material(display_colors: Any, prim_name: str) -> Any:
    """Build a fallback GLTF material from the first displayColor value."""
    c = display_colors[0]
    pbr = pygltflib.PbrMetallicRoughness(baseColorFactor=[float(c[0]), float(c[1]), float(c[2]), 1.0])
    return pygltflib.Material(pbrMetallicRoughness=pbr, name=f"{prim_name}_displayColor", doubleSided=True)


def _get_material_index(
    prim: Any,
    display_colors: Any,
    color_interpolation: Any,
    gltf: Any,
    builder: GLBBuilder,
    texture_cache: dict[tuple[str, str, str], int],
    image_cache: dict[str, int],
    sampler_cache: dict[tuple[int, int], int],
) -> int | None:
    """Resolve GLTF material index from USD bindings or displayColor fallback."""
    mat_index = None
    binding = UsdShade.MaterialBindingAPI(prim).GetDirectBinding()
    if binding:
        material = binding.GetMaterial()
        if material:
            surface_source = material.ComputeSurfaceSource()
            shader = surface_source[0] if surface_source else None
            if shader and shader.GetPrim().IsValid():
                mat = _build_material_from_shader(shader, prim.GetName())
                _apply_preview_surface_textures(
                    shader,
                    mat,
                    gltf,
                    builder,
                    texture_cache,
                    image_cache,
                    sampler_cache,
                )
                mat_index = _append_material_and_get_index(gltf, mat)

    vertex_interp = {UsdGeom.Tokens.vertex, UsdGeom.Tokens.varying}
    if mat_index is None and display_colors:
        if color_interpolation in vertex_interp:
            # Create a white material to properly use vertex colors (COLOR_0)
            pbr = pygltflib.PbrMetallicRoughness(baseColorFactor=[1.0, 1.0, 1.0, 1.0])
            mat = pygltflib.Material(pbrMetallicRoughness=pbr, name=f"{prim.GetName()}_vertexColor", doubleSided=True)
            mat_index = _append_material_and_get_index(gltf, mat)
        else:
            # Use the first color value as a uniform material
            mat = _build_display_color_material(display_colors, prim.GetName())
            mat_index = _append_material_and_get_index(gltf, mat)

    return mat_index


def _append_mesh_to_scene(
    prim: Any, attributes: Any, idx_acc: int, mat_index: int | None, gltf: Any, scene: Any
) -> None:
    """Append one mesh primitive and its node to the active scene."""
    primitive = pygltflib.Primitive(attributes=attributes, indices=idx_acc, material=mat_index)
    gltf_mesh = pygltflib.Mesh(primitives=[primitive], name=prim.GetName())
    gltf.meshes.append(gltf_mesh)

    node = pygltflib.Node(mesh=len(gltf.meshes) - 1, name=prim.GetName())
    gltf.nodes.append(node)
    scene.nodes.append(len(gltf.nodes) - 1)


def _iter_usd_mesh_prims(stage: Any) -> list[Any]:
    """Collect mesh prims from a USD stage."""
    mesh_prims = []
    for prim in stage.Traverse():
        if prim.IsA(UsdGeom.Mesh):
            mesh_prims.append(prim)
    return mesh_prims


def _build_attributes_for_mesh(
    prim: Any,
    usd_mesh: Any,
    builder: GLBBuilder,
) -> tuple[Any, int, Any, Any]:
    """Build geometric attributes and index accessor for one mesh."""
    triangle_positions, triangle_indices, triangle_uvs = _build_triangle_mesh_data(prim, usd_mesh)
    pos_acc = _add_position_attribute(triangle_positions, builder)
    idx_acc = _add_index_accessor(triangle_indices, builder)

    attributes = pygltflib.Attributes(POSITION=pos_acc)
    _add_uv_attribute(prim, attributes, triangle_uvs, builder)

    display_colors, color_interpolation = _get_display_colors(usd_mesh)
    _add_display_color_attribute(
        triangle_positions,
        display_colors,
        color_interpolation,
        attributes,
        builder,
    )
    return attributes, idx_acc, display_colors, color_interpolation


def _resolve_primvar_element_index(
    interpolation: Any,
    face_index: int,
    corner_index: int,
    point_index: int,
) -> int | None:
    """Resolve primvar element index by interpolation for one face corner."""
    if interpolation in {UsdGeom.Tokens.vertex, UsdGeom.Tokens.varying}:
        return point_index
    if interpolation == UsdGeom.Tokens.faceVarying:
        return corner_index
    if interpolation == UsdGeom.Tokens.uniform:
        return face_index
    if interpolation == UsdGeom.Tokens.constant:
        return 0
    return None


def _build_corner_uvs(
    prim: Any, face_vertex_indices: list[int], face_vertex_counts: list[int]
) -> list[tuple[float, float]] | None:
    """Build one UV coordinate per face corner, honoring indexed primvars."""
    st_primvar = UsdGeom.PrimvarsAPI(prim).GetPrimvar("st")
    if not st_primvar or not st_primvar.IsDefined():
        return None

    st_values = st_primvar.Get()
    if not st_values:
        return None

    st_indices = st_primvar.GetIndices() or []
    interpolation = st_primvar.GetInterpolation() or UsdGeom.Tokens.faceVarying

    corner_uvs: list[tuple[float, float]] = []
    corner_offset = 0
    for face_index, count in enumerate(face_vertex_counts):
        for local_corner in range(count):
            corner_index = corner_offset + local_corner
            point_index = face_vertex_indices[corner_index]
            element_index = _resolve_primvar_element_index(interpolation, face_index, corner_index, point_index)
            if element_index is None:
                corner_uvs.append((0.0, 0.0))
                continue

            if st_indices and element_index < len(st_indices):
                element_index = st_indices[element_index]

            if element_index is None or element_index < 0 or element_index >= len(st_values):
                corner_uvs.append((0.0, 0.0))
                continue

            uv = st_values[element_index]
            corner_uvs.append((float(uv[0]), float(uv[1])))

        corner_offset += count

    return corner_uvs


def _build_triangle_mesh_data(
    prim: Any, usd_mesh: Any
) -> tuple[list[Any], list[int], list[tuple[float, float]] | None]:
    """Build triangle-ready vertex data, including expanded UVs for face-varying primvars."""
    points = usd_mesh.GetPointsAttr().Get() or []
    face_vertex_indices = list(usd_mesh.GetFaceVertexIndicesAttr().Get() or [])
    face_vertex_counts = list(usd_mesh.GetFaceVertexCountsAttr().Get() or [])

    if not points or not face_vertex_indices or not face_vertex_counts:
        return points, list(range(len(points))), None

    corner_uvs = _build_corner_uvs(prim, face_vertex_indices, face_vertex_counts)

    triangle_positions: list[Any] = []
    triangle_indices: list[int] = []
    triangle_uvs: list[tuple[float, float]] | None = [] if corner_uvs is not None else None

    corner_offset = 0
    for count in face_vertex_counts:
        if count < 3:
            corner_offset += count
            continue

        for tri_step in range(1, count - 1):
            tri_corners = (0, tri_step, tri_step + 1)
            for local_corner in tri_corners:
                corner_index = corner_offset + local_corner
                point_index = face_vertex_indices[corner_index]
                if point_index < 0 or point_index >= len(points):
                    continue

                point = points[point_index]
                triangle_positions.append(point)
                triangle_indices.append(len(triangle_positions) - 1)

                if triangle_uvs is not None and corner_uvs is not None:
                    triangle_uvs.append(corner_uvs[corner_index])

        corner_offset += count

    return triangle_positions, triangle_indices, triangle_uvs


def _convert_mesh_prim_to_gltf(
    prim: Any,
    gltf: Any,
    scene: Any,
    builder: GLBBuilder,
    texture_cache: dict[tuple[str, str, str], int],
    image_cache: dict[str, int],
    sampler_cache: dict[tuple[int, int], int],
) -> None:
    """Convert one USD mesh prim into GLTF mesh/node entries."""
    usd_mesh = UsdGeom.Mesh(prim)
    points = usd_mesh.GetPointsAttr().Get()
    if not points:
        return

    attributes, idx_acc, display_colors, color_interpolation = _build_attributes_for_mesh(
        prim,
        usd_mesh,
        builder,
    )
    mat_index = _get_material_index(
        prim,
        display_colors,
        color_interpolation,
        gltf,
        builder,
        texture_cache,
        image_cache,
        sampler_cache,
    )
    _append_mesh_to_scene(prim, attributes, idx_acc, mat_index, gltf, scene)


def convert_usd_to_glb(path: Path) -> bytes:
    """Convert a USD stage to a self-contained GLB binary."""
    stage = _open_stage_for_glb(path)
    gltf, scene = _create_gltf_scene()
    builder = GLBBuilder(gltf)
    texture_cache: dict[tuple[str, str, str], int] = {}
    image_cache: dict[str, int] = {}
    sampler_cache: dict[tuple[int, int], int] = {}

    _append_usd_lights_to_scene(stage, gltf, scene)

    for prim in _iter_usd_mesh_prims(stage):
        _convert_mesh_prim_to_gltf(
            prim,
            gltf,
            scene,
            builder,
            texture_cache,
            image_cache,
            sampler_cache,
        )

    return builder.finalize()
