# Briefing

## Omniverse

Omniverse python library is not the appropiate tool for visualization in Python. It serves for OpenUSD modification and scripting for Omniverse GUI.

## OpenUSD Python library

It is possible to view OpenUSD files through Python with this implementation. However, you must build OpenUSD within your python env.
Also, there seems to be compatibility issues with some of the files, not 100% consistent in visualization.


## Datoviz and Vulkan

Since Synopsys uses mainly Vulkan internally, we can integrate Datoviz, which is a VTK equivalent of vulkan, although much less mature.
It is well maintained.

Lines of work:
 - VTK - Datoviz converter.
 - Integrate Datoviz in viz interface.


## VTKHDF format

Still in development, not fully compatible with UnstructuredGrid. A (vtkxml to vtkhdf)[https://gitlab.kitware.com/keu-public/vtkhdf/vtkhdf-scripts/-/tree/main/vtkxml-to-vtkhdf] converter exists, not integrated in PyVista

Lines of work:
- Ask to integrate this tool into PyVista or be published in a different repo.