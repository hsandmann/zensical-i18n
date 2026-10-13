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

from pathlib import Path

from zensical_i18n import staging
from zensical_i18n.settings import load_settings

# ----------------------------------------------------------------------------
# Tests
# ----------------------------------------------------------------------------


def test_collect_default(project: Path) -> None:
    settings = load_settings(project)
    files = staging.collect(settings, settings.default)
    assert sorted(map(str, files)) == [
        "assets/logo.svg",
        "guide/install.md",
        "index.md",
    ]
    assert all(source.fallback is None for source in files.values())


def test_collect_with_fallback(project: Path) -> None:
    settings = load_settings(project)
    files = staging.collect(settings, settings.language("pt"))
    assert sorted(map(str, files)) == [
        "assets/logo.svg",
        "extra.md",
        "guide/install.md",
        "index.md",
    ]
    assert files[Path("index.md")].fallback is None
    assert files[Path("guide/install.md")].fallback == "en"


def test_collect_without_fallback(project: Path) -> None:
    settings = load_settings(project)
    settings.fallback_to_default = False
    files = staging.collect(settings, settings.language("pt"))
    assert Path("guide/install.md") not in files


def test_mark_fallback() -> None:
    assert staging.mark_fallback("# Title\n", "en") == (
        b"---\ni18n_fallback: en\n---\n\n# Title\n"
    )
    assert staging.mark_fallback("---\ntitle: T\n---\n# T\n", "en") == (
        b"---\ni18n_fallback: en\ntitle: T\n---\n# T\n"
    )


def test_page_urls() -> None:
    files = {
        Path(path): staging.Source()
        for path in ["index.md", "a.md", "b/index.md", "b/README.md", "x.png"]
    }
    assert staging.page_urls(files, directory_urls=True) == ["", "a/", "b/"]
    assert staging.page_urls(files, directory_urls=False) == [
        "a.html",
        "b/index.html",
        "index.html",
    ]


def test_sync(project: Path, tmp_path: Path) -> None:
    settings = load_settings(project)
    files = staging.collect(settings, settings.language("pt"))
    dest = tmp_path / "staged"
    assert staging.sync(files, dest)
    assert not staging.sync(files, dest)
    assert (
        dest.joinpath("guide/install.md")
        .read_text()
        .startswith("---\ni18n_fallback: en\n")
    )

    # Files that aren't part of the language anymore are removed
    del files[Path("extra.md")]
    assert staging.sync(files, dest)
    assert not dest.joinpath("extra.md").exists()
