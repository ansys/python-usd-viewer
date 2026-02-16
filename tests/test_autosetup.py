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
"""Unit tests for the autosetup module."""

import os
from unittest.mock import Mock, patch

import pytest

from ansys.tools.usdviewer import autosetup


@patch("ansys.tools.usdviewer.autosetup.Path")
def test_clone_openusd_already_exists(mock_path, tmp_path):
    """Test clone_openusd when repository already exists."""
    mock_path.return_value.exists.return_value = True

    result = autosetup.clone_openusd()

    assert result == "OpenUSD"


@patch("ansys.tools.usdviewer.autosetup.subprocess.run")
@patch("ansys.tools.usdviewer.autosetup.platform.system", return_value="Windows")
@patch("ansys.tools.usdviewer.autosetup.Path")
def test_clone_openusd_success(mock_path, mock_system, mock_run, tmp_path):
    """Test successful cloning of OpenUSD repository."""
    mock_path.return_value.exists.return_value = False
    mock_run.return_value = Mock(returncode=0)

    result = autosetup.clone_openusd()

    assert result == "OpenUSD"
    assert mock_run.call_count >= 2


@patch("ansys.tools.usdviewer.autosetup.subprocess.run")
@patch("ansys.tools.usdviewer.autosetup.platform.system", return_value="Linux")
@patch("ansys.tools.usdviewer.autosetup.Path")
def test_clone_openusd_failure(mock_path, mock_system, mock_run):
    """Test clone_openusd when cloning fails."""
    import subprocess

    mock_path.return_value.exists.return_value = False
    mock_run.side_effect = subprocess.CalledProcessError(1, "git")

    with pytest.raises(RuntimeError, match="Failed to clone OpenUSD"):
        autosetup.clone_openusd()


@patch("ansys.tools.usdviewer.autosetup.subprocess.run")
@patch("ansys.tools.usdviewer.autosetup.Path")
@patch("ansys.tools.usdviewer.autosetup.platform.system", return_value="Windows")
def test_check_build_dependencies_windows_vs_found(mock_system, mock_path, mock_run):
    """Test check_build_dependencies on Windows with Visual Studio found."""
    mock_path_instance = Mock()
    mock_path_instance.exists.return_value = True
    mock_path.return_value = mock_path_instance

    # Mock vswhere calls
    mock_run.side_effect = [
        Mock(stdout="C:\\Program Files\\Microsoft Visual Studio\\2022\\Community", returncode=0),
        Mock(stdout="17", returncode=0),
        Mock(stdout="cmake version 3.28.0", returncode=0),
    ]

    autosetup.check_build_dependencies()


@patch("warnings.warn")
@patch("ansys.tools.usdviewer.autosetup.subprocess.run")
@patch("ansys.tools.usdviewer.autosetup.Path")
@patch("ansys.tools.usdviewer.autosetup.platform.system", return_value="Windows")
def test_check_build_dependencies_windows_vs_2026(mock_system, mock_path, mock_run, mock_warn):
    """Test check_build_dependencies with VS 2026 warning."""
    mock_path_instance = Mock()
    mock_path_instance.exists.return_value = True
    mock_path.return_value = mock_path_instance

    mock_run.side_effect = [
        Mock(stdout="C:\\Program Files\\Microsoft Visual Studio\\2026\\Community", returncode=0),
        Mock(stdout="18", returncode=0),
        Mock(stdout="cmake version 3.28.0", returncode=0),
    ]

    autosetup.check_build_dependencies()
    mock_warn.assert_called()


@patch("warnings.warn")
@patch("ansys.tools.usdviewer.autosetup.Path")
@patch("ansys.tools.usdviewer.autosetup.platform.system", return_value="Windows")
def test_check_build_dependencies_windows_no_vs(mock_system, mock_path, mock_warn):
    """Test check_build_dependencies on Windows without Visual Studio."""
    mock_path_instance = Mock()
    mock_path_instance.exists.return_value = False
    mock_path.return_value = mock_path_instance

    with pytest.raises(RuntimeError, match="C\\+\\+ compiler not found"):
        autosetup.check_build_dependencies()


@patch("ansys.tools.usdviewer.autosetup.subprocess.run")
@patch("ansys.tools.usdviewer.autosetup.platform.system", return_value="Linux")
def test_check_build_dependencies_linux_gcc_found(mock_system, mock_run):
    """Test check_build_dependencies on Linux with gcc found."""
    # Mock both g++ and cmake calls
    mock_run.side_effect = [
        Mock(returncode=0, stdout="g++ version"),
        Mock(returncode=0, stdout="cmake version 3.28.0\n"),
    ]

    autosetup.check_build_dependencies()


@patch("ansys.tools.usdviewer.autosetup.subprocess.run")
@patch("ansys.tools.usdviewer.autosetup.platform.system", return_value="Linux")
def test_check_build_dependencies_linux_no_gcc(mock_system, mock_run):
    """Test check_build_dependencies on Linux without gcc."""
    import subprocess

    mock_run.side_effect = subprocess.CalledProcessError(1, "g++")

    with pytest.raises(RuntimeError, match="C\\+\\+ compiler not found"):
        autosetup.check_build_dependencies()


@patch("ansys.tools.usdviewer.autosetup.subprocess.run")
@patch("ansys.tools.usdviewer.autosetup.platform.system", return_value="Darwin")
def test_check_build_dependencies_macos_clang_found(mock_system, mock_run):
    """Test check_build_dependencies on macOS with clang found."""
    # Mock both clang++ and cmake calls
    mock_run.side_effect = [
        Mock(returncode=0, stdout="clang version"),
        Mock(returncode=0, stdout="cmake version 3.28.0\n"),
    ]

    autosetup.check_build_dependencies()


@patch("ansys.tools.usdviewer.autosetup.subprocess.run")
@patch("ansys.tools.usdviewer.autosetup.platform.system", return_value="Darwin")
def test_check_build_dependencies_macos_no_clang(mock_system, mock_run):
    """Test check_build_dependencies on macOS without clang."""
    import subprocess

    mock_run.side_effect = subprocess.CalledProcessError(1, "clang++")

    with pytest.raises(RuntimeError, match="C\\+\\+ compiler not found"):
        autosetup.check_build_dependencies()


@patch("ansys.tools.usdviewer.autosetup.subprocess.run")
@patch("ansys.tools.usdviewer.autosetup.platform.system", return_value="Linux")
def test_check_build_dependencies_no_cmake(mock_system, mock_run):
    """Test check_build_dependencies without CMake."""
    import subprocess

    # First call for g++ succeeds, second for cmake fails
    mock_run.side_effect = [
        Mock(returncode=0),
        subprocess.CalledProcessError(1, "cmake"),
    ]

    with pytest.raises(RuntimeError, match="CMake not found"):
        autosetup.check_build_dependencies()


@patch.dict(os.environ, {"TEST_VAR": "test_value"})
@patch("ansys.tools.usdviewer.autosetup.platform.system", return_value="Linux")
def test_get_vs_environment_non_windows(mock_system):
    """Test get_vs_environment on non-Windows systems."""
    env = autosetup.get_vs_environment()
    assert env["TEST_VAR"] == "test_value"


@patch.dict(os.environ, {"TEST_VAR": "test_value"})
@patch("ansys.tools.usdviewer.autosetup.Path")
@patch("ansys.tools.usdviewer.autosetup.platform.system", return_value="Windows")
def test_get_vs_environment_windows_no_vswhere(mock_system, mock_path):
    """Test get_vs_environment on Windows without vswhere."""
    mock_path_instance = Mock()
    mock_path_instance.exists.return_value = False
    mock_path.return_value = mock_path_instance

    env = autosetup.get_vs_environment()
    assert env["TEST_VAR"] == "test_value"


@patch("ansys.tools.usdviewer.autosetup.Path")
@patch("tempfile.NamedTemporaryFile")
@patch("ansys.tools.usdviewer.autosetup.subprocess.run")
@patch("ansys.tools.usdviewer.autosetup.platform.system", return_value="Windows")
def test_get_vs_environment_windows_success(mock_system, mock_run, mock_temp, mock_path_class, tmp_path):
    """Test get_vs_environment on Windows with VS environment setup."""
    # Mock vswhere and cmd calls
    mock_run.side_effect = [
        Mock(stdout="C:\\VS\\2022", returncode=0, strip=Mock(return_value="C:\\VS\\2022")),
        Mock(stdout="PATH=C:\\VS\\bin\nINCLUDE=C:\\VS\\include", returncode=0),
    ]

    # Create a real temporary batch file using tmp_path
    temp_bat = tmp_path / "test.bat"
    temp_bat.write_text("")  # Create the file

    # Configure mock to return our temp file path
    mock_file = Mock()
    mock_file.name = str(temp_bat)
    mock_file.__enter__ = Mock(return_value=mock_file)
    mock_file.__exit__ = Mock(return_value=False)
    mock_temp.return_value = mock_file

    # Setup Path mocking
    def path_side_effect(path_str):
        mock_p = Mock()
        if "vswhere" in str(path_str):
            mock_p.exists.return_value = True
        elif "vcvarsall" in str(path_str) or str(path_str) == str(temp_bat):
            mock_p.exists.return_value = True
            mock_p.unlink = Mock()
        else:
            mock_p.exists.return_value = False

            # Support path division for vcvarsall construction
            # Create a mock that always returns a path with exists=True when divided
            def create_chainable_path(*args, **kwargs):
                chained_mock = Mock()
                chained_mock.exists.return_value = True
                chained_mock.__truediv__ = Mock(side_effect=create_chainable_path)
                return chained_mock

            mock_p.__truediv__ = Mock(side_effect=create_chainable_path)
        return mock_p

    mock_path_class.side_effect = path_side_effect

    env = autosetup.get_vs_environment()
    assert "PATH" in env


@patch.dict(os.environ, {"TEST_VAR": "test_value"})
@patch("ansys.tools.usdviewer.autosetup.Path")
@patch("ansys.tools.usdviewer.autosetup.platform.system", return_value="Windows")
def test_get_vs_environment_windows_exception(mock_system, mock_path_class):
    """Test get_vs_environment on Windows with exception during env setup."""
    mock_path = Mock()
    mock_path.exists.return_value = False
    mock_path_class.return_value = mock_path

    # When no VS is found, should return a copy of os.environ
    env = autosetup.get_vs_environment()
    assert env["TEST_VAR"] == "test_value"


def test_build_and_install_openusd_already_exists(tmp_path):
    """Test build_and_install_openusd when installation already exists."""
    install_path = tmp_path / "usd_install"
    (install_path / "lib").mkdir(parents=True)

    result = autosetup.build_and_install_openusd(install_path=install_path, force_rebuild=False)

    assert result == install_path


@patch("ansys.tools.usdviewer.autosetup.shutil.rmtree")
@patch("ansys.tools.usdviewer.autosetup.get_vs_environment")
@patch("ansys.tools.usdviewer.autosetup.subprocess.run")
def test_build_and_install_openusd_success(mock_run, mock_env, mock_rmtree, tmp_path):
    """Test successful build and installation of OpenUSD."""
    install_path = tmp_path / "usd_install"
    mock_run.return_value = Mock(returncode=0)
    mock_env.return_value = os.environ.copy()

    result = autosetup.build_and_install_openusd(install_path=install_path, force_rebuild=True)

    assert result == install_path


@patch("ansys.tools.usdviewer.autosetup.get_vs_environment")
@patch("ansys.tools.usdviewer.autosetup.subprocess.run")
def test_build_and_install_openusd_jinja_install_fails(mock_run, mock_env, tmp_path):
    """Test build_and_install_openusd when Jinja2 installation fails."""
    import subprocess

    install_path = tmp_path / "usd_install"

    # First call for Jinja2 fails, second succeeds for build
    mock_run.side_effect = [
        subprocess.CalledProcessError(1, "pip"),
        Mock(returncode=0),
    ]
    mock_env.return_value = os.environ.copy()

    result = autosetup.build_and_install_openusd(install_path=install_path, force_rebuild=True)
    assert result == install_path


@patch("ansys.tools.usdviewer.autosetup.get_vs_environment")
@patch("ansys.tools.usdviewer.autosetup.subprocess.run")
def test_build_and_install_openusd_build_failure(mock_run, mock_env, tmp_path):
    """Test build_and_install_openusd when build fails."""
    import subprocess

    install_path = tmp_path / "usd_install"

    # First call for Jinja2 succeeds, second fails for build
    mock_run.side_effect = [
        Mock(returncode=0),
        subprocess.CalledProcessError(1, "build_usd.py"),
    ]
    mock_env.return_value = os.environ.copy()

    with pytest.raises(RuntimeError, match="Failed to build OpenUSD"):
        autosetup.build_and_install_openusd(install_path=install_path, force_rebuild=True)


@patch("ansys.tools.usdviewer.autosetup.shutil.rmtree")
@patch("ansys.tools.usdviewer.autosetup.Path")
def test_cleanup_openusd_repo_success(mock_path_class, mock_rmtree):
    """Test successful cleanup of OpenUSD repository."""
    mock_path = Mock()
    mock_path.exists.return_value = True
    mock_path_class.return_value = mock_path

    autosetup.cleanup_openusd_repo("OpenUSD")
    mock_rmtree.assert_called_once()


@patch("ansys.tools.usdviewer.autosetup.shutil.rmtree")
@patch("ansys.tools.usdviewer.autosetup.Path")
def test_cleanup_openusd_repo_not_exists(mock_path_class, mock_rmtree):
    """Test cleanup when repository doesn't exist."""
    mock_path = Mock()
    mock_path.exists.return_value = False
    mock_path_class.return_value = mock_path

    autosetup.cleanup_openusd_repo("OpenUSD")
    mock_rmtree.assert_not_called()


@patch("ansys.tools.usdviewer.autosetup.shutil.rmtree")
@patch("ansys.tools.usdviewer.autosetup.Path")
def test_cleanup_openusd_repo_failure(mock_path_class, mock_rmtree):
    """Test cleanup when removal fails."""
    mock_path = Mock()
    mock_path.exists.return_value = True
    mock_path.absolute.return_value = "/some/path"
    mock_path_class.return_value = mock_path
    mock_rmtree.side_effect = Exception("Permission denied")

    autosetup.cleanup_openusd_repo("OpenUSD")


@patch("sys.argv", ["usd-setup"])
def test_parse_arguments_no_args():
    """Test parse_arguments with no arguments."""
    args = autosetup.parse_arguments()
    assert args.force_rebuild is False


@patch("sys.argv", ["usd-setup", "--force-rebuild"])
def test_parse_arguments_force_rebuild():
    """Test parse_arguments with force_rebuild flag."""
    args = autosetup.parse_arguments()
    assert args.force_rebuild is True


@patch("ansys.tools.usdviewer.autosetup.platform.system", return_value="Windows")
@patch("ansys.tools.usdviewer.autosetup.cleanup_openusd_repo")
@patch("ansys.tools.usdviewer.autosetup.build_and_install_openusd")
@patch("ansys.tools.usdviewer.autosetup.clone_openusd", return_value="OpenUSD")
@patch("ansys.tools.usdviewer.autosetup.check_build_dependencies")
@patch("ansys.tools.usdviewer.autosetup.parse_arguments")
def test_main_success(mock_args, mock_check, mock_clone, mock_build, mock_cleanup, mock_system):
    """Test main function with successful setup."""
    mock_args.return_value = Mock(force_rebuild=False)

    autosetup.main()

    # Verify the correct sequence of operations
    mock_check.assert_called_once()
    mock_clone.assert_called_once()
    mock_build.assert_called_once()
    mock_cleanup.assert_called_once_with("OpenUSD")


@patch("ansys.tools.usdviewer.autosetup.Path")
@patch.dict(os.environ, {"VIRTUAL_ENV": "/path/to/venv"})
@patch("ansys.tools.usdviewer.autosetup.platform.system", return_value="Linux")
@patch("ansys.tools.usdviewer.autosetup.cleanup_openusd_repo")
@patch("ansys.tools.usdviewer.autosetup.build_and_install_openusd")
@patch("ansys.tools.usdviewer.autosetup.clone_openusd", return_value="OpenUSD")
@patch("ansys.tools.usdviewer.autosetup.check_build_dependencies")
@patch("ansys.tools.usdviewer.autosetup.parse_arguments")
def test_main_linux_venv(mock_args, mock_check, mock_clone, mock_build, mock_cleanup, mock_system, mock_path_class):
    """Test main function on Linux with virtual environment."""
    mock_args.return_value = Mock(force_rebuild=False)

    # Mock the path structure for venv
    mock_path = Mock()
    mock_path.exists.return_value = True
    mock_path.glob.return_value = [Mock()]
    mock_path_class.return_value = mock_path

    mock_pth_file = Mock()
    mock_path_class.return_value = mock_pth_file

    autosetup.main()

    # Verify the setup sequence was executed
    mock_check.assert_called_once()
    mock_clone.assert_called_once()
    mock_build.assert_called_once()
    mock_cleanup.assert_called_once_with("OpenUSD")


@patch("builtins.print")
@patch("ansys.tools.usdviewer.autosetup.check_build_dependencies")
@patch("ansys.tools.usdviewer.autosetup.parse_arguments")
def test_main_failure(mock_args, mock_check, mock_print):
    """Test main function with failure."""
    mock_args.return_value = Mock(force_rebuild=False)
    mock_check.side_effect = RuntimeError("Test error")

    with pytest.raises(SystemExit) as exc_info:
        autosetup.main()

    # Verify it exits with error code 1
    assert exc_info.value.code == 1
    # Verify error message was printed
    mock_print.assert_any_call("\n❌ Setup failed: Test error")


@patch("ansys.tools.usdviewer.autosetup.Path")
@patch.dict(os.environ, {"VIRTUAL_ENV": "/path/to/venv"})
@patch("ansys.tools.usdviewer.autosetup.platform.system", return_value="Linux")
@patch("ansys.tools.usdviewer.autosetup.cleanup_openusd_repo")
@patch("ansys.tools.usdviewer.autosetup.build_and_install_openusd")
@patch("ansys.tools.usdviewer.autosetup.clone_openusd", return_value="OpenUSD")
@patch("ansys.tools.usdviewer.autosetup.check_build_dependencies")
@patch("ansys.tools.usdviewer.autosetup.parse_arguments")
def test_main_linux_venv_no_site_packages(
    mock_args, mock_check, mock_clone, mock_build, mock_cleanup, mock_system, mock_path_class
):
    """Test main on Linux with venv but no site-packages."""
    mock_args.return_value = Mock(force_rebuild=False)

    mock_path = Mock()
    mock_python_dir = Mock()
    mock_site_packages = Mock()
    mock_site_packages.exists.return_value = False
    mock_python_dir.__truediv__ = Mock(return_value=mock_site_packages)

    mock_lib_dir = Mock()
    mock_lib_dir.glob.return_value = [mock_python_dir]
    mock_path.__truediv__ = Mock(return_value=mock_lib_dir)
    mock_path_class.return_value = mock_path

    autosetup.main()

    # Verify setup completed even without site-packages
    mock_check.assert_called_once()
    mock_clone.assert_called_once()
    mock_build.assert_called_once()
    mock_cleanup.assert_called_once_with("OpenUSD")


@patch("builtins.print")
@patch("ansys.tools.usdviewer.autosetup.Path")
@patch.dict(os.environ, {"VIRTUAL_ENV": "/path/to/venv"})
@patch("ansys.tools.usdviewer.autosetup.platform.system", return_value="Linux")
@patch("ansys.tools.usdviewer.autosetup.cleanup_openusd_repo")
@patch("ansys.tools.usdviewer.autosetup.build_and_install_openusd")
@patch("ansys.tools.usdviewer.autosetup.clone_openusd", return_value="OpenUSD")
@patch("ansys.tools.usdviewer.autosetup.check_build_dependencies")
@patch("ansys.tools.usdviewer.autosetup.parse_arguments")
def test_main_linux_venv_exception(
    mock_args, mock_check, mock_clone, mock_build, mock_cleanup, mock_system, mock_path_class, mock_print
):
    """Test main on Linux with venv setup exception."""
    mock_args.return_value = Mock(force_rebuild=False)
    mock_path_class.side_effect = Exception("Test exception")

    autosetup.main()

    # Verify the main setup still completed despite venv exception
    mock_check.assert_called_once()
    mock_clone.assert_called_once()
    mock_build.assert_called_once()
    mock_cleanup.assert_called_once_with("OpenUSD")
    # Verify warning about venv setup failure was printed
    assert any(
        "Warning: Could not automatically add USD to Python path" in str(call) for call in mock_print.call_args_list
    )
