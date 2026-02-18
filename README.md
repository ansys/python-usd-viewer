# Python OpenUSD viewer

## Goals
This library allows to visualize VTK-based 3D models (meshes, point clouds, etc.) within the USD viewer,
even though USD and VTK are different 3D formats. The converter acts as a bridge between the 2 ecosystems.

## How does the conversion work?
The `VTKConverter` class handles the VTK assets by:
1. Reading the VTK file using the appropriate VTK reader
2. Converting the VTK geometry data to polydata(surface representation) or at least extract the surface
3. Translating the VTK polydata to a USD mesh
4. Embedding it into a USD stage for visualization

## Installation steps:

### Prerequisites

#### C++ Compiler Requirements

**Windows:**
- **Visual Studio 2022 or earlier** (Community, Professional, Enterprise, or Build Tools)
- **Visual Studio 2026 (version 18) is NOT yet supported** by OpenUSD's build system
- The `usd-setup` script relies on OpenUSD's `build_usd.py`, which currently only supports up to Visual Studio 2022 (version 17)

**Recommended installation:**
- [Visual Studio 2022 Build Tools](https://visualstudio.microsoft.com/downloads/#build-tools-for-visual-studio-2022)
- During installation, select **"Desktop development with C++"**

**Linux/macOS:**
- C++ compiler should be available by default (gcc/g++ on Linux, clang on macOS)

#### Other Requirements
- CMake 3.14 or latery
- Git (for cloning OpenUSD repository)

### Installation Steps

1. Create a new Python environment for this repository.
```bash
pip install uv  # if uv is not installed
uv venv .venv
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
uv sync
```

4. Use the auto installer to setup OpenUSD or follow the instructions in the OpenUSD repository
```bash
usd-setup
```

## Usage

Maya style controls: Press alt to move around with the mouse.
