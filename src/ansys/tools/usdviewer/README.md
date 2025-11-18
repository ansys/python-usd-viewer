# Asset Resolver and VTK Support

This directory contains the asset resolver functionality for the USD Viewer, enabling support for various file formats including VTK files.

## Features

### Asset Resolver
- **Multi-format support**: Load USD, VTK, OBJ, PLY, STL files
- **Search path management**: Configure multiple search paths for asset resolution
- **Automatic conversion**: Convert VTK formats to USD for visualization
- **Asset path resolution**: Resolve relative paths using configured search directories

### VTK Integration
- **VTK to USD conversion**: Convert VTK files to USD format for display
- **Multiple VTK formats**: Support for .vtk, .vtp, .vtu, .vts files
- **3D format support**: Load OBJ, PLY, STL files through VTK
- **Color preservation**: Maintain vertex colors during conversion
- **Mesh geometry**: Convert points, faces, and other geometric data

## Usage Examples

### Basic VTK File Loading

```python
from ansys.tools.usdviewer import USDViewer

# Create viewer with asset search paths
viewer = USDViewer(
    title="VTK Viewer", size=(800, 600), asset_search_paths=["/path/to/assets"]
)

# Load VTK file (automatically converts to USD)
stage = viewer.load_asset("model.vtk")
viewer.show()
```

### Using Asset Resolver Directly

```python
from ansys.tools.usdviewer import AssetResolver

# Create and configure asset resolver
resolver = AssetResolver()
resolver.add_search_path("/path/to/assets")
resolver.add_search_path("/another/path")

# Load asset as USD stage
stage = resolver.load_asset_as_usd("model.vtk")
```

### Converting VTK to USD

```python
from ansys.tools.usdviewer import VTKToUSDConverter

# Convert VTK file to USD
converter = VTKToUSDConverter()
stage = converter.convert_vtk_to_usd("input.vtk", "output.usda")
```

### Advanced Usage with Multiple Formats

```python
from ansys.tools.usdviewer import USDViewer

viewer = USDViewer(asset_search_paths=["./assets"])

# Load different formats
viewer.load_asset("mesh.vtk")  # VTK legacy format
viewer.load_asset("data.vtp")  # VTK XML PolyData
viewer.load_asset("model.obj")  # Wavefront OBJ
viewer.load_asset("scan.ply")  # Stanford PLY
viewer.load_asset("part.stl")  # STL file

viewer.show()
```

## Supported File Formats

| Format | Extension | Description |
|--------|-----------|-------------|
| USD | .usd, .usda, .usdc, .usdz | Universal Scene Description |
| VTK Legacy | .vtk | VTK legacy format |
| VTK XML PolyData | .vtp | VTK XML PolyData format |
| VTK XML Unstructured Grid | .vtu | VTK XML Unstructured Grid |
| VTK XML Structured Grid | .vts | VTK XML Structured Grid |
| Wavefront OBJ | .obj | Wavefront OBJ format |
| Stanford PLY | .ply | Stanford PLY format |
| STL | .stl | STL format |

## API Reference

### AssetResolver

Main class for asset path resolution and format conversion.

#### Methods
- `add_search_path(path)`: Add a directory to search for assets
- `resolve_asset(asset_path)`: Resolve an asset path to a concrete file path
- `load_asset_as_usd(asset_path)`: Load any supported asset as a USD stage
- `register_custom_resolver(stage)`: Register resolver with a USD stage

### VTKToUSDConverter

Utility class for converting VTK files to USD format.

#### Methods
- `convert_vtk_to_usd(vtk_file_path, output_usd_path=None)`: Convert VTK to USD

### USDViewer Extensions

The main USDViewer class has been extended with asset resolver support.

#### New Methods
- `add_asset_search_path(path)`: Add search path for assets
- `load_asset(asset_path)`: Load any supported asset format
- `load_vtk(vtk_path)`: Specific method for loading VTK files

#### New Parameters
- `asset_search_paths`: List of paths to search for assets during initialization

## Installation Requirements

Make sure you have the required dependencies:

```bash
pip install vtk pyside6 numpy
```

For USD support, you'll also need the OpenUSD Python bindings (pxr package).

## Examples

See the examples directory for complete working examples:

- `01-vtk-asset-resolver.py`: Basic VTK file loading
- `02-advanced-asset-resolver.py`: Complex scenes with asset references
- `03-multiple-vtk-formats.py`: Loading different VTK formats

## Troubleshooting

### Common Issues

1. **VTK file not loading**: Ensure the file format is supported and the file is not corrupted
2. **Asset not found**: Check that the asset path is correct and search paths are configured
3. **Conversion errors**: Some VTK files may have unsupported features; check console output for details

### Debug Tips

- Enable verbose output to see asset resolution details
- Check file permissions and paths
- Verify VTK file integrity using VTK tools
