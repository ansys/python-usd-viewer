# Copyright (C) 2025 ANSYS, Inc. and/or its affiliates.
# SPDX-License-Identifier: MIT
#

"""Asset resolver for handling various file types and USD asset paths."""

from pathlib import Path
from typing import Optional, Union

from pxr import Gf, Usd, UsdGeom
import vtk


class _VTKConverter:
    """Convert VTK files to USD format for visualization."""

    @staticmethod
    def convert_vtk_to_usd(vtk_file_path: Union[str, Path], stage: Usd.Stage) -> Usd.Stage:
        """Convert a VTK file to a USD stage.

        Parameters
        ----------
        vtk_file_path : Union[str, Path]
            Path to the VTK file to convert.
        stage : Usd.Stage
            The stage to add the VTK data to.

        Returns
        -------
        Usd.Stage
            The stage containing the VTK data.
        """
        vtk_file_path = Path(vtk_file_path)

        if not vtk_file_path.exists():
            raise FileNotFoundError(f"VTK file not found: {vtk_file_path}")

        # Read VTK file
        reader = _VTKConverter._get_vtk_reader(vtk_file_path)
        reader.SetFileName(str(vtk_file_path))
        reader.Update()

        data = reader.GetOutput()

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
            geometry_filter = vtk.vtkGeometryFilter()
            geometry_filter.SetInputData(data)
            geometry_filter.Update()
            polydata = geometry_filter.GetOutput()

        # Convert VTK polydata to USD mesh with unique name based on file
        mesh_name = vtk_file_path.stem  # Use filename without extension
        _VTKConverter._convert_polydata_to_usd_mesh(polydata, stage, mesh_name)

        return stage

    @staticmethod
    def _get_vtk_reader(file_path: Path):
        """Get appropriate VTK reader based on file extension."""
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
    def _convert_polydata_to_usd_mesh(polydata, stage: Usd.Stage, mesh_name: str = "VTKMesh"):
        """Convert VTK polydata to USD mesh geometry."""
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

    def load_asset(self, asset_path: str, stage: Usd.Stage) -> Optional[Usd.Stage]:
        """Load a VTK asset into the provided stage.

        Parameters
        ----------
        asset_path : str
            Path to the asset file.
        stage : Usd.Stage
            The stage to add the asset to.

        Returns
        -------
        Optional[Usd.Stage]
            The stage with the loaded asset, or None if loading failed.
        """
        resolved_path = None
        direct_path = Path(asset_path)
        if direct_path.exists():
            resolved_path = direct_path.resolve()

        if not resolved_path:
            print(f"Asset not found: {asset_path}")
            return None

        file_extension = resolved_path.suffix.lower()

        # Handle VTK and other 3D formats
        if file_extension in [".vtk", ".vtp", ".vtu", ".vts", ".obj", ".ply", ".stl"]:
            try:
                # Convert VTK data directly into the provided stage
                self.convert_vtk_to_usd(resolved_path, stage)
                return stage
            except Exception as e:
                print(f"Failed to convert VTK file {resolved_path}: {e}")
                return None

        else:
            print(f"Unsupported file format: {file_extension}")
            return None
