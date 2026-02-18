# Copyright (C) 2025 - 2026 ANSYS, Inc. and/or its affiliates.
# SPDX-License-Identifier: MIT
#
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

"""Auto-setup script for OpenUSD installation.

This script creates a virtual environment if needed, clones the OpenUSD repository,
and installs it with all necessary dependencies.
"""

import argparse
import os
from pathlib import Path
import platform
import shutil
import subprocess  # nosec B404 - subprocess is required for build automation with trusted system tools
import sys
import textwrap
import warnings


def clone_openusd() -> str:
    """Clone the OpenUSD repository if it doesn't exist.

    Returns
    -------
    str:
        Path to the cloned repo.
    """
    openusd_path = "OpenUSD"

    if Path(openusd_path).exists():
        print(f"✓ OpenUSD repository already exists at {openusd_path}")
        return openusd_path

    print("Cloning OpenUSD repository...")

    # Enable long path support on Windows
    if platform.system() == "Windows":
        try:
            subprocess.run(["git", "config", "--global", "core.longpaths", "true"], check=True, capture_output=True)  # nosec B603, B607
        except subprocess.CalledProcessError:
            print("Warning: Could not enable git long paths support")

    try:
        # Clone with shallow depth first to avoid some long path issues
        subprocess.run(  # nosec B603, B607
            ["git", "clone", "--depth", "1", "https://github.com/PixarAnimationStudios/OpenUSD.git", str(openusd_path)],
            check=True,
        )

        # Then fetch submodules
        subprocess.run(["git", "submodule", "update", "--init", "--recursive"], cwd=openusd_path, check=True)  # nosec B603, B607

        print(f"✓ OpenUSD repository cloned to {openusd_path}")
        return openusd_path

    except subprocess.CalledProcessError:
        raise RuntimeError(
            "Failed to clone OpenUSD repository. This may be due to Windows path length limitations. "
            "Try enabling long path support in Windows or running from a shorter directory path"
        )


def check_build_dependencies():
    """Check if required build dependencies are available.

    Raises
    ------
    RuntimeError
        If required build dependencies are not found.
    """
    system = platform.system()

    if system == "Windows":
        # Check for Visual Studio or Visual Studio Build Tools
        # Try to find vswhere.exe which is installed with VS2017+
        vswhere_paths = [
            r"C:\Program Files (x86)\Microsoft Visual Studio\Installer\vswhere.exe",
            r"C:\Program Files\Microsoft Visual Studio\Installer\vswhere.exe",
        ]

        vs_found = False
        vs_path = None
        for vswhere_path in vswhere_paths:
            if Path(vswhere_path).exists():
                try:
                    result = subprocess.run(  # nosec B603
                        [vswhere_path, "-latest", "-property", "installationPath"],
                        capture_output=True,
                        text=True,
                        check=True,
                    )
                    vs_path = result.stdout.strip()
                    print(f"Found Visual Studio installation at: {vs_path}")
                    if vs_path:
                        vs_found = True

                        # Check Visual Studio version
                        version_result = subprocess.run(
                            [vswhere_path, "-latest", "-property", "catalog_productLineVersion"],
                            capture_output=True,
                            text=True,
                            check=True,
                        )
                        vs_version = version_result.stdout.strip()
                        print(f"Detected Visual Studio version: {vs_version}")

                        # Check if VS 2026 (version 18) or later
                        if vs_version and int(vs_version) == 18:
                            warning_msg = textwrap.dedent(f"""
                                ⚠️  WARNING: Visual Studio {vs_version} detected

                                OpenUSD's build_usd.py script does NOT yet support Visual Studio 2026 (version 18).
                                The build system currently only supports up to Visual Studio 2022 (version 17).

                                You have two options:

                                1. Install Visual Studio 2022 Build Tools in parallel:
                                   https://visualstudio.microsoft.com/downloads/#build-tools-for-visual-studio-2022

                                   During installation, select "Desktop development with C++"

                                2. Wait for OpenUSD to add support for Visual Studio 2026
                                   (Monitor: https://github.com/PixarAnimationStudios/OpenUSD/issues/3968)

                                The build will likely FAIL with the current Visual Studio version.
                            """)
                            print(warning_msg)
                            warnings.warn(warning_msg)

                        break
                except subprocess.CalledProcessError:
                    continue

        if not vs_found:
            error_msg = textwrap.dedent("""
                ❌ WARNING: C++ compiler not found

                If Microsoft Visual Studio is already installed, ensure that the executables
                are available in your system PATH.

                OpenUSD requires a C++ compiler to build. On Windows, you need to install
                Microsoft Visual Studio or Visual Studio Build Tools.

                ⚠️ IMPORTANT: Visual Studio 2026 (version 18) is NOT yet supported!
                OpenUSD's build_usd.py only supports up to Visual Studio 2022 (version 17).
                Wait for OpenUSD to add support for Visual Studio 2026.

                Please install one of the following:

                1. Visual Studio 2019 or later (Community Edition is free):
                   https://visualstudio.microsoft.com/downloads/

                   During installation, make sure to select:
                   - "Desktop development with C++"

                2. Visual Studio Build Tools (lighter installation):
                   https://visualstudio.microsoft.com/downloads/#build-tools-for-visual-studio-2022

                   During installation, select:
                   - "Desktop development with C++"

                After installation, restart your terminal and run this script again.

                For more information, see:
                https://github.com/PixarAnimationStudios/OpenUSD#getting-and-building-the-code
            """)
            warnings.warn(error_msg)
            raise RuntimeError(error_msg)
        else:
            print("✓ Visual Studio C++ compiler found")

    elif system == "Linux":
        # Check for gcc or g++
        try:
            subprocess.run(["g++", "--version"], capture_output=True, check=True)  # nosec B603, B607
            print("✓ g++ compiler found")
        except (subprocess.CalledProcessError, FileNotFoundError):
            error_msg = textwrap.dedent("""
                ❌ ERROR: C++ compiler not found

                OpenUSD requires a C++ compiler to build. On Linux, you need gcc/g++.

                Please install using your package manager:

                Ubuntu/Debian:
                  sudo apt-get install build-essential

                Fedora/RHEL/CentOS:
                  sudo yum groupinstall "Development Tools"

                After installation, run this script again.
            """)
            raise RuntimeError(error_msg)

    elif system == "Darwin":  # macOS
        # Check for clang (Xcode command line tools)
        try:
            subprocess.run(["clang++", "--version"], capture_output=True, check=True)  # nosec B603, B607
            print("✓ clang++ compiler found")
        except (subprocess.CalledProcessError, FileNotFoundError):
            error_msg = textwrap.dedent("""
                ❌ ERROR: C++ compiler not found

                OpenUSD requires a C++ compiler to build. On macOS, you need Xcode Command Line Tools.

                Please install by running:
                  xcode-select --install

                After installation, run this script again.
            """)
            raise RuntimeError(error_msg)

    # Check for CMake
    try:
        result = subprocess.run(["cmake", "--version"], capture_output=True, check=True, text=True)  # nosec B603, B607
        cmake_version = result.stdout.split("\n")[0]
        print(f"✓ CMake found: {cmake_version}")
    except (subprocess.CalledProcessError, FileNotFoundError):
        error_msg = textwrap.dedent("""
            ❌ ERROR: CMake not found

            OpenUSD requires CMake to build.

            Please install CMake from: https://cmake.org/download/

            Or use a package manager:
            - Windows: choco install cmake (requires Chocolatey)
            - macOS: brew install cmake (requires Homebrew)
            - Linux: sudo apt-get install cmake (Ubuntu/Debian)

            After installation, run this script again.
        """)
        raise RuntimeError(error_msg)


def get_vs_environment() -> dict:
    """Get Visual Studio environment variables on Windows.

    Returns
    -------
    dict
        Environment variables with Visual Studio paths added.
    """
    if platform.system() != "Windows":
        return os.environ.copy()

    # Find Visual Studio installation
    vswhere_paths = [
        r"C:\Program Files (x86)\Microsoft Visual Studio\Installer\vswhere.exe",
        r"C:\Program Files\Microsoft Visual Studio\Installer\vswhere.exe",
    ]

    vs_path = None
    for vswhere_path in vswhere_paths:
        if Path(vswhere_path).exists():
            try:
                result = subprocess.run(  # nosec B603
                    [vswhere_path, "-latest", "-property", "installationPath"],
                    capture_output=True,
                    text=True,
                    check=True,
                )
                vs_path = result.stdout.strip()
                if vs_path:
                    break
            except subprocess.CalledProcessError:
                continue

    if not vs_path:
        return os.environ.copy()

    # Find vcvarsall.bat
    vcvarsall = Path(vs_path) / "VC" / "Auxiliary" / "Build" / "vcvarsall.bat"
    if not vcvarsall.exists():
        return os.environ.copy()

    # Run vcvarsall.bat and capture the environment
    # We use a batch script to set up VS environment and echo it
    try:
        import tempfile

        with tempfile.NamedTemporaryFile(mode="w", suffix=".bat", delete=False) as f:
            f.write("@echo off\n")
            f.write(f'call "{vcvarsall}" x64 > nul\n')
            f.write("set\n")
            temp_bat = f.name

        result = subprocess.run(["cmd", "/c", temp_bat], capture_output=True, text=True, check=True)  # nosec B603, B607

        # Parse the environment variables
        env = os.environ.copy()
        for line in result.stdout.splitlines():
            if "=" in line:
                key, _, value = line.partition("=")
                env[key] = value

        Path(temp_bat).unlink()
        print("✓ Visual Studio environment configured")
        return env

    except Exception as e:
        print(f"⚠️  Warning: Could not set up Visual Studio environment: {e}")
        return os.environ.copy()


def build_and_install_openusd(install_path: Path = None, force_rebuild: bool = False) -> Path:
    """Build and install OpenUSD using the build script."""
    # Create build directory
    install_path = install_path if install_path else Path("usd_install")

    # Check if already built and not forcing rebuild
    if not force_rebuild and install_path.exists() and (install_path / "lib").exists():
        print(f"✓ OpenUSD installation already exists at {install_path}")
        print("  Use --force-rebuild to rebuild from scratch")
        return install_path

    print("Building and installing OpenUSD... This may take a while (30+ minutes)")

    # Install optional dependencies for schema generation tools
    try:
        print("Installing optional Python dependencies (Jinja2)...")
        subprocess.run([sys.executable, "-m", "uv", "pip", "install", "jinja2"], capture_output=True, check=True)  # nosec B603
        print("✓ Jinja2 installed (enables usdGenSchema tools)")
    except subprocess.CalledProcessError:
        print("⚠️  Warning: Could not install Jinja2. Schema generation tools will be omitted.")

    # Clean previous builds if they exist or if forcing rebuild
    if install_path.exists():
        shutil.rmtree(install_path)

    install_path.mkdir(exist_ok=True)

    # Build OpenUSD using the build_usd.py script
    build_script = Path("OpenUSD") / "build_scripts" / "build_usd.py"

    try:
        # Get Visual Studio environment on Windows
        env = get_vs_environment()

        cmd = [
            sys.executable,  # Use the current Python interpreter
            str(build_script),
            str(install_path),
            "--build-variant",
            "release",
            "--no-docs",  # Skip documentation to speed up build
            "--no-examples",  # Skip examples to speed up build
            "--no-tutorials",  # Skip tutorials to speed up build
        ]

        print(f"Running: {' '.join(cmd)}")

        # Run the build with Visual Studio environment
        subprocess.run(cmd, env=env, check=True)  # nosec B603

        print("✓ OpenUSD built and installed successfully")

        # Add installation instructions
        print("\n" + "=" * 60)
        print("INSTALLATION COMPLETE!")
        print("=" * 60)
        print(f"OpenUSD has been installed to: {install_path}")
        return install_path

    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"Failed to build OpenUSD: {e}")


def cleanup_openusd_repo(openusd_path):
    """Clean up the cloned OpenUSD repository after successful installation."""
    if Path(openusd_path).exists():
        print(f"Cleaning up cloned repository at {openusd_path}...")
        try:
            shutil.rmtree(openusd_path)
            print("✓ OpenUSD repository cleaned up successfully")
        except Exception as e:
            print(f"⚠️  Warning: Could not remove OpenUSD repository: {e}")
            print(f"   You can manually delete the directory: {Path(openusd_path).absolute()}")


def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        prog="usd-setup",
        description="Auto-setup script for OpenUSD installation with USD Viewer project.",
        epilog="This script will create a virtual environment, clone OpenUSD, and build it for your project.",
    )

    parser.add_argument(
        "--force-rebuild", action="store_true", help="Force rebuild of OpenUSD even if it already exists"
    )

    return parser.parse_args()


def main():
    """Run the OpenUSD auto-setup process."""
    args = parse_arguments()

    print("🚀 Starting OpenUSD auto-setup...")
    print("=" * 60)

    try:
        # Check build dependencies first
        print("\n📋 Checking build dependencies...")
        check_build_dependencies()

        # Clone OpenUSD
        print("\n📦 Setting up OpenUSD repository...")
        openusd_path = clone_openusd()

        # Build and install OpenUSD
        print("\n🔨 Building OpenUSD...")
        build_and_install_openusd(force_rebuild=args.force_rebuild)
        cleanup_openusd_repo(openusd_path)

        print("\n✅ Setup completed successfully!")

        # Add USD to Python path automatically if in a Linux virtual environment
        if platform.system() == "Linux":
            venv_path = os.environ.get("VIRTUAL_ENV")
            if venv_path:
                try:
                    # Get current working directory and construct USD lib path
                    usd_lib_path = Path.cwd() / "usd_install" / "lib" / "python"

                    # Find the site-packages directory in the virtual environment
                    venv_path = Path(venv_path)
                    lib_dir = venv_path / "lib"
                    python_dirs = list(lib_dir.glob("python*"))

                    if python_dirs:
                        site_packages = python_dirs[0] / "site-packages"

                        if site_packages.exists():
                            pth_file = site_packages / "usd.pth"
                            pth_file.write_text(str(usd_lib_path) + "\n")
                            print(f"✓ Added USD to Python path via {pth_file}")
                        else:
                            print("⚠️  Could not find site-packages directory in virtual environment")
                    else:
                        print("⚠️  Could not find Python version directory in virtual environment")

                except Exception as e:
                    print(f"⚠️  Warning: Could not automatically add USD to Python path: {e}")
                    usd_path = Path.cwd() / "usd_install" / "lib" / "python"
                    print(f"   You may need to manually add {usd_path} to your PYTHONPATH")

    except Exception as e:
        print(f"\n❌ Setup failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
