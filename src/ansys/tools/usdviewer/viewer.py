"""
MIT License
Copyright (c) 2019 Roy Nieterau
Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:
The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.
THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

import sys
import numpy as np
from PySide6 import QtGui, QtCore, QtWidgets
from pxr import Usd, UsdUtils, Sdf, Gf
from pxr.Usdviewq.stageView import StageView


class Widget(QtWidgets.QWidget):
    def __init__(self, stage=None):
        super(Widget, self).__init__()
        self.model = StageView.DefaultDataModel()
        
        self.view = StageView(dataModel=self.model)
        
        layout = QtWidgets.QVBoxLayout(self)
        layout.addWidget(self.view)
        layout.setContentsMargins(0, 0, 0, 0)
        
        if stage:
            self.setStage(stage)
        
    def setStage(self, stage):
        self.model.stage = stage
                              
    def closeEvent(self, event):
        # Ensure to close the renderer to avoid GlfPostPendingGLErrors
        self.view.closeRenderer()

class USDViewer():
    def __init__(self, title: str = "Viewer", size: tuple[int, int] = (750, 750)):
        self._app = QtWidgets.QApplication([])

        self._title = title
        self._size = size


    def plot(self, stage):
        self.window = Widget(stage)
        self.window.setWindowTitle(self._title)
        self.window.resize(QtCore.QSize(*self._size))

    def show(self):
        self.window.show()
        self._app.exec()

    def load_usd(self, path: str) -> Usd.Stage:
        """Load a USD stage from the given file path."""
        with Usd.StageCacheContext(UsdUtils.StageCache.Get()):
            stage = Usd.Stage.Open(path)

        if stage:
            print(f"Stage loaded: {stage.GetRootLayer().GetDisplayName()}")
            
            # Create simplified stage for better compatibility with StageView
            simplified_stage = self._create_simplified_stage(stage)

            if simplified_stage:
                print("Using simplified stage (WarpComputationAPI removed)")
                stage = simplified_stage
            else:
                print("Using original stage")
        else:
            print("Failed to load stage!")
            sys.exit(1)

        # plot the stage
        self.plot(stage)

    def _copy_lights_to_stage(self, source_stage, target_stage):
        """Copy all DistantLight prims from source to target stage."""
        for prim in source_stage.Traverse():
            if prim.GetTypeName() == "DistantLight":
                light_path = prim.GetPath()
                new_light = target_stage.DefinePrim(light_path, "DistantLight")
                
                # Copy light attributes
                for attr in prim.GetAttributes():
                    if attr.Get() is not None:
                        new_attr = new_light.CreateAttribute(attr.GetName(), attr.GetTypeName())
                        new_attr.Set(attr.Get())

    def _find_best_time_code(self, stage, expected_mesh_count=2):
        """Find the best time code where all expected meshes have valid geometry."""
        for time_code in [100.0, 200.0, 300.0, 50.0, 0.0]:
            valid_meshes = 0
            for prim in stage.Traverse():
                if prim.GetTypeName() == "Mesh":
                    points_attr = prim.GetAttribute("points")
                    if points_attr:
                        points = points_attr.Get(time_code)
                        if points and len(points) > 0 and not np.allclose(np.array(points), 0):
                            valid_meshes += 1
            
            if valid_meshes >= expected_mesh_count:
                return time_code
        
        return None

    def _copy_mesh_geometry(self, source_mesh, target_mesh, time_code):
        """Copy mesh geometry data (points, faces, counts) at the specified time code."""
        points_attr = source_mesh.GetAttribute("points")
        faces_attr = source_mesh.GetAttribute("faceVertexIndices")
        counts_attr = source_mesh.GetAttribute("faceVertexCounts")
        
        if points_attr:
            points = points_attr.Get(time_code)
            faces = faces_attr.Get(time_code) if faces_attr else None
            counts = counts_attr.Get(time_code) if counts_attr else None
            
            if points and len(points) > 0 and not np.allclose(np.array(points), 0):
                # Set mesh geometry
                target_mesh.CreateAttribute("points", Sdf.ValueTypeNames.Point3fArray).Set(points)
                if faces:
                    target_mesh.CreateAttribute("faceVertexIndices", Sdf.ValueTypeNames.IntArray).Set(faces)
                if counts:
                    target_mesh.CreateAttribute("faceVertexCounts", Sdf.ValueTypeNames.IntArray).Set(counts)
                return True
        
        return False

    def _copy_transform_attributes(self, source_mesh, target_mesh, time_code):
        """Copy transform attributes from source to target mesh."""
        xform_attrs = ["xformOp:translate", "xformOp:orient", "xformOp:scale"]
        xform_order = []
        
        for attr_name in xform_attrs:
            attr = source_mesh.GetAttribute(attr_name)
            if attr:
                value = attr.Get(time_code) or attr.Get()
                if value is not None:
                    new_attr = target_mesh.CreateAttribute(attr_name, attr.GetTypeName())
                    new_attr.Set(value)
                    xform_order.append(attr_name)
        
        if xform_order:
            target_mesh.CreateAttribute("xformOpOrder", Sdf.ValueTypeNames.TokenArray).Set(xform_order)

    def _create_simplified_stage(self, original_stage):
        """Create a simplified USD stage without WarpComputationAPI for better compatibility."""
        simple_stage = Usd.Stage.CreateInMemory()
        
        # Set up root
        root_prim = simple_stage.DefinePrim("/root", "Xform")
        simple_stage.SetDefaultPrim(root_prim)
        
        # Copy lights
        self._copy_lights_to_stage(original_stage, simple_stage)
        
        # Find best time code with valid geometry
        best_time_code = self._find_best_time_code(original_stage)
        if best_time_code is None:
            return None
        
        # Create simplified meshes
        mesh_count = 0
        for prim in original_stage.Traverse():
            if prim.GetTypeName() == "Mesh":
                mesh_path = prim.GetPath()
                new_mesh = simple_stage.DefinePrim(mesh_path, "Mesh")
                
                # Copy geometry and transforms
                if self._copy_mesh_geometry(prim, new_mesh, best_time_code):
                    self._copy_transform_attributes(prim, new_mesh, best_time_code)
                    mesh_count += 1
        
        return simple_stage if mesh_count > 0 else None

    def _setup_camera(self, view):
        """Position camera to show both rabbit meshes optimally."""
        camera = view.gfCamera
        if camera:
            # Position camera to see both rabbits (one at origin, one offset in Y)
            eye = Gf.Vec3d(0, 12, 50)
            target = Gf.Vec3d(0, 12, 0)
            up = Gf.Vec3d(0, 1, 0)
            
            forward = (target - eye).GetNormalized()
            right = Gf.Cross(forward, up).GetNormalized()
            camera_up = Gf.Cross(right, forward)
            
            transform_matrix = Gf.Matrix4d(
                right[0], camera_up[0], -forward[0], eye[0],
                right[1], camera_up[1], -forward[1], eye[1],
                right[2], camera_up[2], -forward[2], eye[2],
                0, 0, 0, 1
            )
            
            camera.transform = transform_matrix
            
            try:
                camera.SetFieldOfView(60.0)
            except:
                pass  # Field of view adjustment is optional

    def _initialize_view(self):
        self.window.view.updateView(resetCam=True, forceComputeBBox=True)
        self._setup_camera(self.window.view)
        self.window.view.updateView()
        # Initialize view after a short delay
        QtCore.QTimer.singleShot(200, self._initialize_view)









