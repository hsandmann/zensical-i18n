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

import os
from pathlib import Path

import pytest

from zensical_i18n import staging
from zensical_i18n.settings import I18nError, load_settings

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


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        # Byte order marks are removed, so front matter is detected
        (
            "\ufeff---\ntitle: T\n---\n",
            "---\ni18n_fallback: en\ntitle: T\n---\n",
        ),
        # Front matter with Windows line endings
        (
            "---\r\ntitle: T\r\n---\r\n",
            "---\r\ni18n_fallback: en\ntitle: T\r\n---\r\n",
        ),
        # A leading rule without closing fence isn't front matter
        ("---\n\nText\n", "---\ni18n_fallback: en\n---\n\n---\n\nText\n"),
    ],
)
def test_mark_fallback_edge_cases(text: str, expected: str) -> None:
    assert staging.mark_fallback(text, "en") == expected.encode()


def test_encode_url() -> None:
    # Encodings were taken from the sitemap Zensical generates
    assert staging.encode_url("with space/") == "with%20space/"
    assert staging.encode_url("ünï/") == "%C3%BCn%C3%AF/"
    assert staging.encode_url("c#sharp/") == "c%23sharp/"
    assert staging.encode_url("a+b&c=d/") == "a+b%26c=d/"
    assert staging.encode_url("tilde~/") == "tilde%7E/"
    assert staging.encode_url('it\'s "q"/') == "it's%20%22q%22/"
    assert staging.encode_url("100%/") == "100%25/"


def test_sync_detects_changes_within_a_second(tmp_path: Path) -> None:
    src = tmp_path / "page.md"
    src.write_text("* item")
    dest = tmp_path / "staged"
    files = {Path("page.md"): staging.Source(src)}
    staging.sync(files, dest)

    # Same size, modified within the same second
    stat = src.stat()
    src.write_text("- item")
    os.utime(src, ns=(stat.st_atime_ns, stat.st_mtime_ns + 1000))
    assert staging.sync(files, dest)
    assert dest.joinpath("page.md").read_text() == "- item"


def test_sync_removes_symlinks(tmp_path: Path) -> None:
    outside = tmp_path / "outside"
    outside.mkdir()
    outside.joinpath("keep.txt").write_text("keep")
    src = tmp_path / "page.md"
    src.write_text("# Page")
    dest = tmp_path / "staged"
    dest.mkdir()
    dest.joinpath("sub").symlink_to(outside)

    # Writes don't follow the link, and files outside are untouched
    staging.sync({Path("sub/page.md"): staging.Source(src)}, dest)
    assert not dest.joinpath("sub").is_symlink()
    assert dest.joinpath("sub/page.md").read_text() == "# Page"
    assert sorted(p.name for p in outside.iterdir()) == ["keep.txt"]


def test_sync_tolerates_vanished_files(tmp_path: Path) -> None:
    files = {Path("gone.md"): staging.Source(tmp_path / "gone.md")}
    staging.sync(files, tmp_path / "staged")
    assert not tmp_path.joinpath("staged/gone.md").exists()


def test_locale_folder_case(project: Path) -> None:
    docs = project.parent / "docs"
    docs.joinpath("pt").rename(docs / "PT")
    settings = load_settings(project)
    with pytest.raises(I18nError, match="named 'pt'"):
        staging.collect(settings, settings.language("pt"))


def test_page_sources(project: Path) -> None:
    settings = load_settings(project)
    sources = staging.page_sources(settings, settings.language("pt"))
    assert sources["guide/install/"] == staging.Page("guide/install.md", False)
    assert sources[""] == staging.Page("index.md", True)
