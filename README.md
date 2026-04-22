# Python USD Viewer

**Python USD Viewer** allows you to view OpenUSD files and convert VTK objects to OpenUSD objects. 

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
pip install uv
```

2. Create a virtual environment and install the project:
```bash
uv venv .venv
```

3. Activate the environment:

```bash
# On Linux or macOS
source .venv/bin/activate
```

```bash
# On Windows
.venv\Scripts\activate
```

3. Install the project:

```bash
uv sync
```

4. Set up OpenUSD using the OpenUSD auto-installer:

```bash
usd-setup
```

Or, follow the instructions in the OpenUSD repository.

## Usage

Python USD Viewer uses Maya-style controls. To move the camera with the mouse, press and hold the **Alt** key.
