# Copyright (c) 2026 Humberto Sandmann and contributors

# SPDX-License-Identifier: MIT
# All contributions are certified under the DCO

# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to
# deal in the Software without restriction, including without limitation the
# rights to use, copy, modify, merge, publish, distribute, sublicense, and/or
# sell copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NON-INFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
# FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS
# IN THE SOFTWARE.

from __future__ import annotations

from typing import TYPE_CHECKING

from click.testing import CliRunner

from zensical_i18n import __version__
from zensical_i18n.main import cli

if TYPE_CHECKING:
    from pathlib import Path

    import pytest

# ----------------------------------------------------------------------------
# Tests
# ----------------------------------------------------------------------------


def test_version() -> None:
    result = CliRunner().invoke(cli, ["--version"])
    assert result.exit_code == 0
    assert result.output.strip() == __version__


def test_missing_config(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    result = CliRunner().invoke(cli, ["build"])
    assert result.exit_code == 1
    assert "No config file found" in result.output


def test_invalid_config(project: Path) -> None:
    config = project.read_text().replace(
        "[project]\n", '[project]\nsite_dir = "."\n', 1
    )
    project.write_text(config)
    result = CliRunner().invoke(cli, ["build", "-f", str(project)])
    assert result.exit_code == 1
    assert "site_dir must be a folder within project root" in result.output
    assert project.exists()


def test_unknown_locale(project: Path) -> None:
    result = CliRunner().invoke(cli, ["build", "-f", str(project), "-l", "xx"])
    assert result.exit_code == 1
    assert "Unknown or disabled locales" in result.output


def test_build(project: Path) -> None:
    result = CliRunner().invoke(cli, ["build", "-f", str(project), "-l", "pt"])
    assert result.exit_code == 0, result.output
    assert project.parent.joinpath("site/pt/index.html").is_file()
