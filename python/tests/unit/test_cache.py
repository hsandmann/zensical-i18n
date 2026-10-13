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

from zensical_i18n.builder import CACHE_ACTIVE, _command, _replace, cache
from zensical_i18n.settings import load_settings

if TYPE_CHECKING:
    from pathlib import Path

# ----------------------------------------------------------------------------
# Tests
# ----------------------------------------------------------------------------


def test_cache_is_swapped(project: Path) -> None:
    settings = load_settings(project)
    current = settings.root / ".cache"
    current.mkdir()
    current.joinpath("owner").write_text("project")

    # Inside, Zensical sees the language's cache
    with cache(settings, settings.language("pt")):
        assert not current.exists()
        current.mkdir()
        current.joinpath("owner").write_text("pt")

    # Afterwards, the project's cache is back, and the language's is stored
    assert current.joinpath("owner").read_text() == "project"
    with cache(settings, settings.language("pt")):
        assert current.joinpath("owner").read_text() == "pt"


def test_cache_recovers_from_interruption(project: Path) -> None:
    settings = load_settings(project)
    current = settings.root / ".cache"
    current.mkdir()
    current.joinpath("owner").write_text("project")

    # Simulate a run that was killed while the language's cache was active
    context = cache(settings, settings.language("pt"))
    context.__enter__()
    current.mkdir()
    current.joinpath("owner").write_text("pt")
    assert settings.work_dir.joinpath("cache", CACHE_ACTIVE).exists()

    # The next run puts everything back in place first
    with cache(settings, settings.language("en")):
        assert not current.exists()
    assert current.joinpath("owner").read_text() == "project"
    stored = settings.work_dir / "cache" / "pt" / "owner"
    assert stored.read_text() == "pt"


def test_cache_ignores_tampered_marker(project: Path) -> None:
    settings = load_settings(project)
    outside = project.parent / "outside"
    outside.mkdir()
    outside.joinpath("keep.txt").write_text("keep")
    current = settings.root / ".cache"
    current.mkdir()

    # A marker naming a path instead of a locale must not be followed
    caches = settings.work_dir / "cache"
    caches.mkdir(parents=True)
    caches.joinpath(CACHE_ACTIVE).write_text(str(outside))
    with cache(settings, settings.language("pt")):
        pass
    assert outside.joinpath("keep.txt").read_text() == "keep"


def test_replace_keeps_hidden_files(tmp_path: Path) -> None:
    src = tmp_path / "src"
    src.mkdir()
    src.joinpath("index.html").write_text("new")
    dest = tmp_path / "dest"
    dest.joinpath(".git").mkdir(parents=True)
    dest.joinpath(".nojekyll").write_text("")
    dest.joinpath("stale.html").write_text("old")

    _replace(src, dest, keep_hidden=True)
    assert dest.joinpath(".git").is_dir()
    assert dest.joinpath(".nojekyll").exists()
    assert not dest.joinpath("stale.html").exists()
    assert dest.joinpath("index.html").read_text() == "new"


def test_command_isolates_project_modules(project: Path) -> None:
    settings = load_settings(project)
    command = _command("build", settings, settings.default, {})
    assert command[1:3] == ["-P", "-m"]
