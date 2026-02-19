# Python USD Viewer

## Goals
The Python USD Viewer lets you visualize VTK-based 3D models (such as meshes and point clouds), even though USD and VTK are different 3D formats. This library converts between the two ecosystems.

## How the conversion works

The `_VTKConverter` class processes VTK assets by performing these steps:

1. Reads the VTK file using the appropriate VTK reader.
2. Converts the VTK geometry data to polydata (surface representation) or at least extracts the surface.
3. Translates the VTK polydata to a USD mesh.
4. Embeds the USD mesh into a USD stage for visualization.

## Installation

**Prerequisites**

You must have a C++ compiler. Linux typically includes one by default. On Windows, you can use Visual Studio.

1. Create a new Python environment for this repository:

```bash
python -m venv .venv
```

2. Activate the environment:

```bash
# On Linux or macOS
source .venv/bin/activate
```

```bash
# On Windows
.venv/Scripts/activate
```

3. Install the project:

```bash
pip install .
```

4. Set up OpenUSD using the OpenUSD auto-installer:

```bash
usd-setup
```

Or, follow the instructions in the OpenUSD repository.

## Usage

Python USD Viewer uses Maya-style controls. To move the camera with the mouse, press and hold the **Alt** key.
