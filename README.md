# Python OpenUSD viewer

## Goals
This library allows to visualize VTK-based 3D models (meshes, point clouds, etc.) within the USD viewer,
even though USD and VTK are different 3D formats. The converter acts as a bridge between the 2 ecosystems.

## How does the convertion work?
the `_VTKConverter` class handles the VTK assets by:
1. Reading the VTK file using the appropriate VTK reader
2. Converting the VTK geometry data to polydata(surface representation) or at least extract the surface
3. Translating the VTK polydata to a USD mesh
4. Embedding it into a USD stage for visualization


## Installation steps:
Prerequisites: Have C++ compiler (Visual Studio in Windows, should be available by default in Linux)

1.- Create a new Python environment for this repository.
```bash
python -m venv .venv

```
2.- Activate the environment:
    linux
    ```bash
        source .venv/bin/activate
    ```

    windows
    ```bash
        .venv/Scripts/activate
    ```

3.- Install the project:
```bash
pip install .
```

4.- Clone the OpenUSD repo.
```bash
git clone https://github.com/PixarAnimationStudios/OpenUSD.git

```

4.- Build OpenUSD from binaries.
```bash
python OpenUSD/build_scripts/build_usd.py /path/to/my_usd_install_dir
```



## Usage

Maya style controls: Press alt to move around with the mouse.
