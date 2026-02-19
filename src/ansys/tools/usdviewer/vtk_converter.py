# Copyright (C) 2025 - 2026 ANSYS, Inc. and/or its affiliates.
# SPDX-License-Identifier: MIT
#

"""Asset resolver for handling various file types and USD asset paths."""

from pathlib import Path
from typing import Optional, Union
import warnings

try:
    from pxr import Gf, Usd, UsdGeom
except ImportError:
    warnings.warn(
        "The 'pxr' module is required to use the USDViewer. "
        "Install the 'usd-core' package. "
        "For installation instructions, see the documentation."
    )
import vtk


class VTKConverter:
    """Convert VTK files to USD format for visualization."""

    @staticmethod
    def convert_vtk_file_to_usd(vtk_file_path: Union[str, Path], stage: "Usd.Stage" = None) -> None:
        """Convert a VTK file to a USD file.

        Parameters
        ----------
        vtk_file_path : Union[str, Path]
            Path to the VTK file to convert.
        stage : Usd.Stage
            Stage to add the converted USD data to.
        """
        vtk_file_path = Path(vtk_file_path)
        mesh_name = vtk_file_path.stem  # Use filename without extension

        if not vtk_file_path.exists():
            raise FileNotFoundError(f"VTK file not found: {vtk_file_path}")

        # Read VTK file
        reader = VTKConverter.get_vtk_reader(vtk_file_path)
        reader.SetFileName(str(vtk_file_path))
        reader.Update()

        return VTKConverter.convert_vtk_to_usd(reader.GetOutput(), stage, mesh_name)

    @staticmethod
    def convert_vtk_to_usd(
        data: "vtk.vtkDataSet", stage: "Usd.Stage" = None, mesh_name: str = "VTKMesh"
    ) -> "Usd.Stage":
        """Convert a VTK file to a USD stage.

        Parameters
        ----------
        vtk_file_path : Union[str, Path]
            Path to the VTK file to convert.
        stage : Usd.Stage
            Stage to add the VTK data to.

        Returns
        -------
        Usd.Stage
            Stage containing the VTK data.
        """
        if stage is None:
            stage = Usd.Stage.CreateNew("temp.usda")

        # Convert to polydata if necessary
        if isinstance(data, vtk.vtkPolyData):
            polydata = data
        elif isinstance(data, vtk.vtkUnstructuredGrid):
            # Convert unstructured grid to polydata
            geometry_filter = vtk.vtkGeometryFilter()
            geometry_filter.SetInputData(data)
            geometry_filter.Update()
            polydata = geometry_filter.GetOutput()
        else:
            # Try to extract surface from other data types
            try:
                geometry_filter = vtk.vtkGeometryFilter()
                geometry_filter.SetInputData(data)
                geometry_filter.Update()
                polydata = geometry_filter.GetOutput()
            except Exception as e:
                raise ValueError(f"Unable to convert VTK data type {type(data).__name__} to polydata: {e}")

        # Convert VTK polydata to USD mesh with unique name based on file
        VTKConverter.convert_polydata_to_usd_mesh(polydata, stage, mesh_name)

        return stage

    @staticmethod
    def get_vtk_reader(file_path: Path) -> vtk.vtkAlgorithm:
        """Get the appropriate VTK reader based on the file extension.

        Parameters
        ----------
        file_path : Path
            Path to the VTK file.
        """
        extension = file_path.suffix.lower()

        if extension == ".vtk":
            return vtk.vtkPolyDataReader()
        elif extension == ".vtp":
            return vtk.vtkXMLPolyDataReader()
        elif extension == ".vtu":
            return vtk.vtkXMLUnstructuredGridReader()
        elif extension == ".vts":
            return vtk.vtkXMLStructuredGridReader()
        elif extension == ".obj":
            return vtk.vtkOBJReader()
        elif extension == ".ply":
            return vtk.vtkPLYReader()
        elif extension == ".stl":
            return vtk.vtkSTLReader()
        else:
            raise ValueError(f"Unsupported VTK file format: {extension}")

    @staticmethod
    def convert_polydata_to_usd_mesh(
        polydata: vtk.vtkPolyData, stage: "Usd.Stage" = None, mesh_name: str = "VTKMesh"
    ) -> None:
        """Convert VTK polydata to USD mesh geometry.

        Parameters
        ----------
        polydata : vtk.vtkPolyData
            VTK polydata to convert.
        stage : Usd.Stage
            USD stage to add the mesh to.
        mesh_name : str, default: ``"VTKMesh"``
            Name of the mesh in USD.
        """
        if stage is None:
            stage = Usd.Stage.CreateNew("temp.usda")

        # Create a mesh primitive in USD with unique name
        mesh_path = f"/{mesh_name}"
        mesh_prim = UsdGeom.Mesh.Define(stage, mesh_path)

        # Get points from VTK
        points = polydata.GetPoints()
        if points:
            num_points = points.GetNumberOfPoints()
            point_array = []
            for i in range(num_points):
                point = points.GetPoint(i)
                point_array.append(Gf.Vec3f(point[0], point[1], point[2]))

            mesh_prim.CreatePointsAttr().Set(point_array)

        # Get faces from VTK
        polys = polydata.GetPolys()
        if polys:
            face_vertex_indices = []
            face_vertex_counts = []

            polys.InitTraversal()
            id_list = vtk.vtkIdList()

            while polys.GetNextCell(id_list):
                num_vertices = id_list.GetNumberOfIds()
                face_vertex_counts.append(num_vertices)

                for i in range(num_vertices):
                    face_vertex_indices.append(id_list.GetId(i))

            mesh_prim.CreateFaceVertexIndicesAttr().Set(face_vertex_indices)
            mesh_prim.CreateFaceVertexCountsAttr().Set(face_vertex_counts)

        # Handle colors if available
        point_data = polydata.GetPointData()
        if point_data and point_data.GetScalars():
            scalars = point_data.GetScalars()
            if scalars.GetNumberOfComponents() >= 3:
                colors = []
                for i in range(scalars.GetNumberOfTuples()):
                    color = scalars.GetTuple(i)
                    if scalars.GetNumberOfComponents() == 3:
                        colors.append(Gf.Vec3f(color[0], color[1], color[2]))
                    else:  # RGBA
                        colors.append(Gf.Vec3f(color[0], color[1], color[2]))

                # Normalize colors if they're in 0-255 range
                if any(c > 1.0 for color in colors for c in color):
                    colors = [Gf.Vec3f(c[0] / 255.0, c[1] / 255.0, c[2] / 255.0) for c in colors]

                mesh_prim.CreateDisplayColorAttr().Set(colors)

    @staticmethod
    def convert_usd_to_vtk(stage: "Usd.Stage", mesh_path: Optional[str] = None) -> Optional[vtk.vtkPolyData]:
        """Convert a USD mesh to VTK polydata.

        Parameters
        ----------
        stage : Usd.Stage
            USD stage containing the mesh.
        mesh_path : str, default: None
            Path to the mesh in USD. If ``None``, the first mesh in the stage is used.

        Returns
        -------
        Optional[vtk.vtkPolyData]
            Converted VTK polydata or ``None`` if conversion failed.
        """
        # If no mesh path is provided, find the first mesh in the stage
        if mesh_path is None:
            for prim in stage.Traverse():
                if prim.IsA(UsdGeom.Mesh):
                    mesh_path = str(prim.GetPath())
                    break

            if mesh_path is None:
                warnings.warn("No mesh found in the USD stage.")
                return None

        mesh_prim = stage.GetPrimAtPath(mesh_path)
        if not mesh_prim or not mesh_prim.IsA(UsdGeom.Mesh):
            warnings.warn(f"Mesh not found or invalid: {mesh_path}")
            return None

        mesh = UsdGeom.Mesh(mesh_prim)

        # Create a new VTK polydata object
        polydata = vtk.vtkPolyData()

        # Convert points
        points_attr = mesh.GetPointsAttr()
        if points_attr:
            points = points_attr.Get()
            if points:
                vtk_points = vtk.vtkPoints()
                for point in points:
                    vtk_points.InsertNextPoint(point[0], point[1], point[2])
                polydata.SetPoints(vtk_points)

        # Convert faces
        face_vertex_indices_attr = mesh.GetFaceVertexIndicesAttr()
        face_vertex_counts_attr = mesh.GetFaceVertexCountsAttr()

        if face_vertex_indices_attr and face_vertex_counts_attr:
            face_vertex_indices = face_vertex_indices_attr.Get()
            face_vertex_counts = face_vertex_counts_attr.Get()

            if face_vertex_indices and face_vertex_counts:
                vtk_faces = vtk.vtkCellArray()
                start = 0
                for count in face_vertex_counts:
                    vtk_faces.InsertNextCell(count, face_vertex_indices[start : start + count])
                    start += count
                polydata.SetPolys(vtk_faces)

        # Convert colors
        display_color_attr = mesh.GetDisplayColorAttr()
        if display_color_attr:
            colors = display_color_attr.Get()
            if colors:
                vtk_colors = vtk.vtkUnsignedCharArray()
                vtk_colors.SetNumberOfComponents(3)
                vtk_colors.SetName("Colors")

                for color in colors:
                    # USD colors are typically in 0-1 range, convert to 0-255 for VTK
                    r = int(color[0] * 255) if color[0] <= 1.0 else int(color[0])
                    g = int(color[1] * 255) if color[1] <= 1.0 else int(color[1])
                    b = int(color[2] * 255) if color[2] <= 1.0 else int(color[2])
                    vtk_colors.InsertNextTuple3(r, g, b)

                polydata.GetPointData().SetScalars(vtk_colors)

        return polydata

    def load_asset(self, asset_path: str, stage: "Usd.Stage") -> Optional["Usd.Stage"]:
        """Load a VTK asset into a given stage.

        Parameters
        ----------
        asset_path : str
            Path to the asset file.
        stage : Usd.Stage
            Stage to add the asset to.

        Returns
        -------
        Optional[Usd.Stage]
            Stage with the loaded asset or ``None`` if loading failed.
        """
        # Resolve and validate the asset path
        asset_file = Path(asset_path)
        if not asset_file.exists():
            warnings.warn(f"Asset not found: {asset_path}")
            return None

        resolved_path = asset_file.resolve()
        file_extension = resolved_path.suffix.lower()

        # Check if file format is supported
        supported_formats = [".vtk", ".vtp", ".vtu", ".vts", ".obj", ".ply", ".stl"]
        if file_extension not in supported_formats:
            warnings.warn(f"Unsupported file format: {file_extension}")
            return None

        # Convert VTK data directly into the provided stage
        try:
            self.convert_vtk_to_usd(resolved_path, stage)
            return stage
        except (FileNotFoundError, ValueError) as e:
            warnings.warn(f"Failed to convert VTK file {resolved_path}: {e}")
            return None
        except Exception as e:
            warnings.warn(f"Unexpected error converting {resolved_path}: {e}")
            return None
