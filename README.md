# Python OpenUSD viewer


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