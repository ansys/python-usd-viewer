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


def test_clone_openusd_already_exists(tmp_path):
    """Test clone_openusd when repository already exists."""
    with patch("ansys.tools.usdviewer.autosetup.Path") as mock_path:
        mock_path.return_value.exists.return_value = True

        result = autosetup.clone_openusd()

        assert result == "OpenUSD"


def test_clone_openusd_success(tmp_path):
    """Test successful cloning of OpenUSD repository."""
    with patch("ansys.tools.usdviewer.autosetup.Path") as mock_path:
        mock_path.return_value.exists.return_value = False

        with patch("ansys.tools.usdviewer.autosetup.platform.system", return_value="Windows"):
            with patch("ansys.tools.usdviewer.autosetup.subprocess.run") as mock_run:
                mock_run.return_value = Mock(returncode=0)

                result = autosetup.clone_openusd()

                assert result == "OpenUSD"
                assert mock_run.call_count >= 2


def test_clone_openusd_failure():
    """Test clone_openusd when cloning fails."""
    with patch("ansys.tools.usdviewer.autosetup.Path") as mock_path:
        mock_path.return_value.exists.return_value = False

        with patch("ansys.tools.usdviewer.autosetup.platform.system", return_value="Linux"):
            with patch("ansys.tools.usdviewer.autosetup.subprocess.run") as mock_run:
                import subprocess

                mock_run.side_effect = subprocess.CalledProcessError(1, "git")

                with pytest.raises(RuntimeError, match="Failed to clone OpenUSD"):
                    autosetup.clone_openusd()


def test_check_build_dependencies_windows_vs_found():
    """Test check_build_dependencies on Windows with Visual Studio found."""
    with patch("ansys.tools.usdviewer.autosetup.platform.system", return_value="Windows"):
        with patch("ansys.tools.usdviewer.autosetup.Path") as mock_path:
            mock_path_instance = Mock()
            mock_path_instance.exists.return_value = True
            mock_path.return_value = mock_path_instance

            with patch("ansys.tools.usdviewer.autosetup.subprocess.run") as mock_run:
                # Mock vswhere calls
                mock_run.side_effect = [
                    Mock(stdout="C:\\Program Files\\Microsoft Visual Studio\\2022\\Community", returncode=0),
                    Mock(stdout="17", returncode=0),
                    Mock(stdout="cmake version 3.28.0", returncode=0),
                ]

                autosetup.check_build_dependencies()


def test_check_build_dependencies_windows_vs_2026():
    """Test check_build_dependencies with VS 2026 warning."""
    with patch("ansys.tools.usdviewer.autosetup.platform.system", return_value="Windows"):
        with patch("ansys.tools.usdviewer.autosetup.Path") as mock_path:
            mock_path_instance = Mock()
            mock_path_instance.exists.return_value = True
            mock_path.return_value = mock_path_instance

            with patch("ansys.tools.usdviewer.autosetup.subprocess.run") as mock_run:
                mock_run.side_effect = [
                    Mock(stdout="C:\\Program Files\\Microsoft Visual Studio\\2026\\Community", returncode=0),
                    Mock(stdout="18", returncode=0),
                    Mock(stdout="cmake version 3.28.0", returncode=0),
                ]

                with patch("warnings.warn") as mock_warn:
                    autosetup.check_build_dependencies()
                    mock_warn.assert_called()


def test_check_build_dependencies_windows_no_vs():
    """Test check_build_dependencies on Windows without Visual Studio."""
    with patch("ansys.tools.usdviewer.autosetup.platform.system", return_value="Windows"):
        with patch("ansys.tools.usdviewer.autosetup.Path") as mock_path:
            mock_path_instance = Mock()
            mock_path_instance.exists.return_value = False
            mock_path.return_value = mock_path_instance

            with patch("warnings.warn"):
                with pytest.raises(RuntimeError, match="C\\+\\+ compiler not found"):
                    autosetup.check_build_dependencies()


def test_check_build_dependencies_linux_gcc_found():
    """Test check_build_dependencies on Linux with gcc found."""
    with patch("ansys.tools.usdviewer.autosetup.platform.system", return_value="Linux"):
        with patch("ansys.tools.usdviewer.autosetup.subprocess.run") as mock_run:
            # Mock both g++ and cmake calls
            mock_run.side_effect = [
                Mock(returncode=0, stdout="g++ version"),
                Mock(returncode=0, stdout="cmake version 3.28.0\n"),
            ]

            autosetup.check_build_dependencies()


def test_check_build_dependencies_linux_no_gcc():
    """Test check_build_dependencies on Linux without gcc."""
    with patch("ansys.tools.usdviewer.autosetup.platform.system", return_value="Linux"):
        with patch("ansys.tools.usdviewer.autosetup.subprocess.run") as mock_run:
            import subprocess

            mock_run.side_effect = subprocess.CalledProcessError(1, "g++")

            with pytest.raises(RuntimeError, match="C\\+\\+ compiler not found"):
                autosetup.check_build_dependencies()


def test_check_build_dependencies_macos_clang_found():
    """Test check_build_dependencies on macOS with clang found."""
    with patch("ansys.tools.usdviewer.autosetup.platform.system", return_value="Darwin"):
        with patch("ansys.tools.usdviewer.autosetup.subprocess.run") as mock_run:
            # Mock both clang++ and cmake calls
            mock_run.side_effect = [
                Mock(returncode=0, stdout="clang version"),
                Mock(returncode=0, stdout="cmake version 3.28.0\n"),
            ]

            autosetup.check_build_dependencies()


def test_check_build_dependencies_macos_no_clang():
    """Test check_build_dependencies on macOS without clang."""
    with patch("ansys.tools.usdviewer.autosetup.platform.system", return_value="Darwin"):
        with patch("ansys.tools.usdviewer.autosetup.subprocess.run") as mock_run:
            import subprocess

            mock_run.side_effect = subprocess.CalledProcessError(1, "clang++")

            with pytest.raises(RuntimeError, match="C\\+\\+ compiler not found"):
                autosetup.check_build_dependencies()


def test_check_build_dependencies_no_cmake():
    """Test check_build_dependencies without CMake."""
    with patch("ansys.tools.usdviewer.autosetup.platform.system", return_value="Linux"):
        with patch("ansys.tools.usdviewer.autosetup.subprocess.run") as mock_run:
            import subprocess

            # First call for g++ succeeds, second for cmake fails
            mock_run.side_effect = [
                Mock(returncode=0),
                subprocess.CalledProcessError(1, "cmake"),
            ]

            with pytest.raises(RuntimeError, match="CMake not found"):
                autosetup.check_build_dependencies()


def test_get_vs_environment_non_windows():
    """Test get_vs_environment on non-Windows systems."""
    with patch("ansys.tools.usdviewer.autosetup.platform.system", return_value="Linux"):
        with patch.dict(os.environ, {"TEST_VAR": "test_value"}):
            env = autosetup.get_vs_environment()
            assert env["TEST_VAR"] == "test_value"


def test_get_vs_environment_windows_no_vswhere():
    """Test get_vs_environment on Windows without vswhere."""
    with patch("ansys.tools.usdviewer.autosetup.platform.system", return_value="Windows"):
        with patch("ansys.tools.usdviewer.autosetup.Path") as mock_path:
            mock_path_instance = Mock()
            mock_path_instance.exists.return_value = False
            mock_path.return_value = mock_path_instance

            with patch.dict(os.environ, {"TEST_VAR": "test_value"}):
                env = autosetup.get_vs_environment()
                assert env["TEST_VAR"] == "test_value"


def test_get_vs_environment_windows_success(tmp_path):
    """Test get_vs_environment on Windows with VS environment setup."""
    with patch("ansys.tools.usdviewer.autosetup.platform.system", return_value="Windows"):
        # We need to carefully mock Path to return actual string when divided
        with patch("ansys.tools.usdviewer.autosetup.subprocess.run") as mock_run:
            # Mock vswhere and cmd calls
            mock_run.side_effect = [
                Mock(stdout="C:\\VS\\2022", returncode=0, strip=Mock(return_value="C:\\VS\\2022")),
                Mock(stdout="PATH=C:\\VS\\bin\nINCLUDE=C:\\VS\\include", returncode=0),
            ]

            # Create a real temporary batch file using tmp_path
            temp_bat = tmp_path / "test.bat"
            temp_bat.write_text("")  # Create the file

            with patch("ansys.tools.usdviewer.autosetup.tempfile.NamedTemporaryFile") as mock_temp:
                # Configure mock to return our temp file path
                mock_file = Mock()
                mock_file.name = str(temp_bat)
                mock_file.__enter__ = Mock(return_value=mock_file)
                mock_file.__exit__ = Mock(return_value=False)
                mock_temp.return_value = mock_file

                with patch("ansys.tools.usdviewer.autosetup.Path") as mock_path_class:
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


def test_get_vs_environment_windows_exception():
    """Test get_vs_environment on Windows with exception during env setup."""
    with patch("ansys.tools.usdviewer.autosetup.platform.system", return_value="Windows"):
        # Patch Path to always return False for exists to skip VS path finding
        with patch("ansys.tools.usdviewer.autosetup.Path") as mock_path_class:
            mock_path = Mock()
            mock_path.exists.return_value = False
            mock_path_class.return_value = mock_path

            with patch.dict(os.environ, {"TEST_VAR": "test_value"}):
                # When no VS is found, should return a copy of os.environ
                env = autosetup.get_vs_environment()
                assert env["TEST_VAR"] == "test_value"


def test_build_and_install_openusd_already_exists(tmp_path):
    """Test build_and_install_openusd when installation already exists."""
    install_path = tmp_path / "usd_install"
    (install_path / "lib").mkdir(parents=True)

    result = autosetup.build_and_install_openusd(install_path=install_path, force_rebuild=False)

    assert result == install_path


def test_build_and_install_openusd_success(tmp_path):
    """Test successful build and installation of OpenUSD."""
    install_path = tmp_path / "usd_install"

    with patch("ansys.tools.usdviewer.autosetup.subprocess.run") as mock_run:
        mock_run.return_value = Mock(returncode=0)

        with patch("ansys.tools.usdviewer.autosetup.get_vs_environment") as mock_env:
            mock_env.return_value = os.environ.copy()

            with patch("ansys.tools.usdviewer.autosetup.shutil.rmtree"):
                result = autosetup.build_and_install_openusd(install_path=install_path, force_rebuild=True)

                assert result == install_path


def test_build_and_install_openusd_jinja_install_fails(tmp_path):
    """Test build_and_install_openusd when Jinja2 installation fails."""
    install_path = tmp_path / "usd_install"

    with patch("ansys.tools.usdviewer.autosetup.subprocess.run") as mock_run:
        import subprocess

        # First call for Jinja2 fails, second succeeds for build
        mock_run.side_effect = [
            subprocess.CalledProcessError(1, "pip"),
            Mock(returncode=0),
        ]

        with patch("ansys.tools.usdviewer.autosetup.get_vs_environment") as mock_env:
            mock_env.return_value = os.environ.copy()

            result = autosetup.build_and_install_openusd(install_path=install_path, force_rebuild=True)
            assert result == install_path


def test_build_and_install_openusd_build_failure(tmp_path):
    """Test build_and_install_openusd when build fails."""
    install_path = tmp_path / "usd_install"

    with patch("ansys.tools.usdviewer.autosetup.subprocess.run") as mock_run:
        import subprocess

        # First call for Jinja2 succeeds, second fails for build
        mock_run.side_effect = [
            Mock(returncode=0),
            subprocess.CalledProcessError(1, "build_usd.py"),
        ]

        with patch("ansys.tools.usdviewer.autosetup.get_vs_environment") as mock_env:
            mock_env.return_value = os.environ.copy()

            with pytest.raises(RuntimeError, match="Failed to build OpenUSD"):
                autosetup.build_and_install_openusd(install_path=install_path, force_rebuild=True)


def test_cleanup_openusd_repo_success():
    """Test successful cleanup of OpenUSD repository."""
    with patch("ansys.tools.usdviewer.autosetup.Path") as mock_path_class:
        mock_path = Mock()
        mock_path.exists.return_value = True
        mock_path_class.return_value = mock_path

        with patch("ansys.tools.usdviewer.autosetup.shutil.rmtree") as mock_rmtree:
            autosetup.cleanup_openusd_repo("OpenUSD")
            mock_rmtree.assert_called_once()


def test_cleanup_openusd_repo_not_exists():
    """Test cleanup when repository doesn't exist."""
    with patch("ansys.tools.usdviewer.autosetup.Path") as mock_path_class:
        mock_path = Mock()
        mock_path.exists.return_value = False
        mock_path_class.return_value = mock_path

        with patch("ansys.tools.usdviewer.autosetup.shutil.rmtree") as mock_rmtree:
            autosetup.cleanup_openusd_repo("OpenUSD")
            mock_rmtree.assert_not_called()


def test_cleanup_openusd_repo_failure():
    """Test cleanup when removal fails."""
    with patch("ansys.tools.usdviewer.autosetup.Path") as mock_path_class:
        mock_path = Mock()
        mock_path.exists.return_value = True
        mock_path.absolute.return_value = "/some/path"
        mock_path_class.return_value = mock_path

        with patch("ansys.tools.usdviewer.autosetup.shutil.rmtree") as mock_rmtree:
            mock_rmtree.side_effect = Exception("Permission denied")

            autosetup.cleanup_openusd_repo("OpenUSD")


def test_parse_arguments_no_args():
    """Test parse_arguments with no arguments."""
    with patch("sys.argv", ["usd-setup"]):
        args = autosetup.parse_arguments()
        assert args.force_rebuild is False


def test_parse_arguments_force_rebuild():
    """Test parse_arguments with force_rebuild flag."""
    with patch("sys.argv", ["usd-setup", "--force-rebuild"]):
        args = autosetup.parse_arguments()
        assert args.force_rebuild is True


def test_main_success():
    """Test main function with successful setup."""
    with patch("ansys.tools.usdviewer.autosetup.parse_arguments") as mock_args:
        mock_args.return_value = Mock(force_rebuild=False)

        with patch("ansys.tools.usdviewer.autosetup.check_build_dependencies") as mock_check:
            with patch("ansys.tools.usdviewer.autosetup.clone_openusd", return_value="OpenUSD") as mock_clone:
                with patch("ansys.tools.usdviewer.autosetup.build_and_install_openusd") as mock_build:
                    with patch("ansys.tools.usdviewer.autosetup.cleanup_openusd_repo") as mock_cleanup:
                        with patch("ansys.tools.usdviewer.autosetup.platform.system", return_value="Windows"):
                            autosetup.main()

                            # Verify the correct sequence of operations
                            mock_check.assert_called_once()
                            mock_clone.assert_called_once()
                            mock_build.assert_called_once()
                            mock_cleanup.assert_called_once_with("OpenUSD")


def test_main_linux_venv():
    """Test main function on Linux with virtual environment."""
    with patch("ansys.tools.usdviewer.autosetup.parse_arguments") as mock_args:
        mock_args.return_value = Mock(force_rebuild=False)

        with patch("ansys.tools.usdviewer.autosetup.check_build_dependencies") as mock_check:
            with patch("ansys.tools.usdviewer.autosetup.clone_openusd", return_value="OpenUSD") as mock_clone:
                with patch("ansys.tools.usdviewer.autosetup.build_and_install_openusd") as mock_build:
                    with patch("ansys.tools.usdviewer.autosetup.cleanup_openusd_repo") as mock_cleanup:
                        with patch("ansys.tools.usdviewer.autosetup.platform.system", return_value="Linux"):
                            with patch.dict(os.environ, {"VIRTUAL_ENV": "/path/to/venv"}):
                                with patch("ansys.tools.usdviewer.autosetup.Path") as mock_path_class:
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


def test_main_failure():
    """Test main function with failure."""
    with patch("ansys.tools.usdviewer.autosetup.parse_arguments") as mock_args:
        mock_args.return_value = Mock(force_rebuild=False)

        with patch("ansys.tools.usdviewer.autosetup.check_build_dependencies") as mock_check:
            mock_check.side_effect = RuntimeError("Test error")

            with patch("builtins.print") as mock_print:
                with pytest.raises(SystemExit) as exc_info:
                    autosetup.main()

                # Verify it exits with error code 1
                assert exc_info.value.code == 1
                # Verify error message was printed
                mock_print.assert_any_call("Error: Test error")


def test_main_linux_venv_no_site_packages():
    """Test main on Linux with venv but no site-packages."""
    with patch("ansys.tools.usdviewer.autosetup.parse_arguments") as mock_args:
        mock_args.return_value = Mock(force_rebuild=False)

        with patch("ansys.tools.usdviewer.autosetup.check_build_dependencies") as mock_check:
            with patch("ansys.tools.usdviewer.autosetup.clone_openusd", return_value="OpenUSD") as mock_clone:
                with patch("ansys.tools.usdviewer.autosetup.build_and_install_openusd") as mock_build:
                    with patch("ansys.tools.usdviewer.autosetup.cleanup_openusd_repo") as mock_cleanup:
                        with patch("ansys.tools.usdviewer.autosetup.platform.system", return_value="Linux"):
                            with patch.dict(os.environ, {"VIRTUAL_ENV": "/path/to/venv"}):
                                with patch("ansys.tools.usdviewer.autosetup.Path") as mock_path_class:
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


def test_main_linux_venv_exception():
    """Test main on Linux with venv setup exception."""
    with patch("ansys.tools.usdviewer.autosetup.parse_arguments") as mock_args:
        mock_args.return_value = Mock(force_rebuild=False)

        with patch("ansys.tools.usdviewer.autosetup.check_build_dependencies") as mock_check:
            with patch("ansys.tools.usdviewer.autosetup.clone_openusd", return_value="OpenUSD") as mock_clone:
                with patch("ansys.tools.usdviewer.autosetup.build_and_install_openusd") as mock_build:
                    with patch("ansys.tools.usdviewer.autosetup.cleanup_openusd_repo") as mock_cleanup:
                        with patch("ansys.tools.usdviewer.autosetup.platform.system", return_value="Linux"):
                            with patch.dict(os.environ, {"VIRTUAL_ENV": "/path/to/venv"}):
                                with patch("ansys.tools.usdviewer.autosetup.Path") as mock_path_class:
                                    mock_path_class.side_effect = Exception("Test exception")

                                    with patch("builtins.print") as mock_print:
                                        autosetup.main()

                                        # Verify the main setup still completed despite venv exception
                                        mock_check.assert_called_once()
                                        mock_clone.assert_called_once()
                                        mock_build.assert_called_once()
                                        mock_cleanup.assert_called_once_with("OpenUSD")
                                        # Verify warning about venv setup failure was printed
                                        assert any(
                                            "virtual environment" in str(call).lower() or "venv" in str(call).lower()
                                            for call in mock_print.call_args_list
                                        )
