# Copyright (C) 2025 ANSYS, Inc. and/or its affiliates.
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
import subprocess
import sys


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
            subprocess.run(["git", "config", "--global", "core.longpaths", "true"], check=True, capture_output=True)
        except subprocess.CalledProcessError:
            print("Warning: Could not enable git long paths support")

    try:
        # Clone with shallow depth first to avoid some long path issues
        subprocess.run(
            ["git", "clone", "--depth", "1", "https://github.com/PixarAnimationStudios/OpenUSD.git", str(openusd_path)],
            check=True,
        )

        # Then fetch submodules
        subprocess.run(["git", "submodule", "update", "--init", "--recursive"], cwd=openusd_path, check=True)

        print(f"✓ OpenUSD repository cloned to {openusd_path}")
        return openusd_path

    except subprocess.CalledProcessError:
        raise RuntimeError(
            "Failed to clone OpenUSD repository. This may be due to Windows path length limitations. "
            "Try enabling long path support in Windows or running from a shorter directory path"
        )


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

    # Clean previous builds if they exist or if forcing rebuild
    if install_path.exists():
        shutil.rmtree(install_path)

    install_path.mkdir(exist_ok=True)

    # Build OpenUSD using the build_usd.py script
    build_script = Path("OpenUSD") / "build_scripts" / "build_usd.py"

    try:
        cmd = [
            "python",
            str(build_script),
            str(install_path),
            "--build-variant",
            "release",
            "--no-docs",  # Skip documentation to speed up build
            "--no-examples",  # Skip examples to speed up build
            "--no-tutorials",  # Skip tutorials to speed up build
        ]
        os.system(" ".join(cmd))

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
        # Clone OpenUSD
        openusd_path = clone_openusd()

        # Build and install OpenUSD
        build_and_install_openusd(args.force_rebuild)

        # Clean up the cloned repository unless user wants to keep it
        if not args.keep_repo:
            cleanup_openusd_repo(openusd_path)

        print("\n✅ Setup completed successfully!")

    except Exception as e:
        print(f"\n❌ Setup failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
