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

import json
from typing import TYPE_CHECKING
from xml.etree import ElementTree

import pytest
from bs4 import BeautifulSoup

from zensical_i18n import builder, discovery
from zensical_i18n.settings import load_settings

if TYPE_CHECKING:
    from pathlib import Path

# ----------------------------------------------------------------------------
# Constants
# ----------------------------------------------------------------------------

# Site URL and edit links of the fixture project.
BASE = "https://example.com/docs/"
EDIT = "https://github.com/o/r/edit/main/docs"

# ----------------------------------------------------------------------------
# Fixtures
# ----------------------------------------------------------------------------


@pytest.fixture
def site(suffix_project: Path) -> Path:
    """Build the fixture project with the suffix structure."""
    builder.build(load_settings(suffix_project))
    return suffix_project.parent / "site"


# ----------------------------------------------------------------------------
# Helpers
# ----------------------------------------------------------------------------


def _soup(path: Path) -> BeautifulSoup:
    return BeautifulSoup(path.read_text(), "html.parser")


def _edit(path: Path) -> str:
    link = _soup(path).select_one("a[rel=edit]")
    assert link is not None
    return str(link["href"])


# ----------------------------------------------------------------------------
# Tests
# ----------------------------------------------------------------------------


def test_structure(site: Path) -> None:
    for path in [
        "index.html",
        "guide/install/index.html",
        "pt/index.html",
        "pt/guide/install/index.html",
        "pt/extra/index.html",
        "assets/app.min.js",
        "pt/assets/app.min.js",
    ]:
        assert site.joinpath(path).is_file(), path
    assert not site.joinpath("extra").exists()
    assert not site.joinpath("index.pt").exists()
    assert not any(site.rglob("*.pt.*"))


def test_translations(site: Path) -> None:
    pt = _soup(site / "pt/index.html")
    assert pt.title is not None
    assert pt.title.get_text() == "Início - Documentação"
    assert pt.select_one(".md-i18n-notice") is None
    titles = [title.get_text() for title in pt.select(".admonition-title")]
    assert titles == ["Nota"]

    # Pages without translation fall back to the default language
    fallback = _soup(site / "pt/guide/install/index.html")
    assert fallback.select_one(".md-i18n-notice") is not None


def test_localized_assets(site: Path) -> None:
    assert site.joinpath("assets/logo.png").read_text() == "logo-en"
    assert site.joinpath("pt/assets/logo.png").read_text() == "logo-pt"


def test_edit_links(site: Path) -> None:
    assert _edit(site / "index.html") == f"{EDIT}/index.md"
    assert _edit(site / "pt/index.html") == f"{EDIT}/index.pt.md"
    assert _edit(site / "pt/extra/index.html") == f"{EDIT}/extra.pt.md"
    assert _edit(site / "pt/guide/install/index.html") == (
        f"{EDIT}/guide/install.md"
    )


def test_sitemaps_and_manifest(site: Path) -> None:
    ns = {"s": discovery.SITEMAP_NS, "x": discovery.XHTML_NS}
    root = ElementTree.parse(site / "pt/sitemap.xml").getroot()  # noqa: S314
    alternates = {
        url.findtext("s:loc", "", ns): {
            str(link.get("hreflang")) for link in url.findall("x:link", ns)
        }
        for url in root.findall("s:url", ns)
    }
    assert alternates[f"{BASE}pt/"] == {"en", "pt", "x-default"}
    assert alternates[f"{BASE}pt/guide/install/"] == set()

    manifest = json.loads((site / "zensical-i18n.json").read_text())
    assert manifest["pages"] == {
        "en": ["", "guide/install/"],
        "pt": ["", "extra/", "guide/install/"],
    }


def test_links_to_suffixed_files(suffix_project: Path) -> None:
    docs = suffix_project.parent / "docs"
    docs.joinpath("index.pt.md").write_text(
        "# Início\n\n[Extra](extra.pt.md)\n\n![Logo](assets/logo.pt.png)\n"
    )
    # Zensical validates links before they're resolved, and reports links
    # to suffixed pages as invalid, but they work in the site
    builder.build(load_settings(suffix_project))
    soup = _soup(suffix_project.parent / "site/pt/index.html")
    content = soup.select_one("article")
    assert content is not None
    assert content.select_one("a[href='extra/']") is not None
    assert content.select_one("img[src='assets/logo.png']") is not None


@pytest.mark.parametrize("fixture", ["project", "suffix_project"])
def test_partial_builds_are_identical(
    fixture: str, request: pytest.FixtureRequest
) -> None:
    config: Path = request.getfixturevalue(fixture)
    text = config.read_text()
    if "repo_url" not in text:
        text = text.replace(
            "[project]\n",
            '[project]\nrepo_url = "https://github.com/o/r"\n',
            1,
        ).replace(
            'features = ["navigation.instant"]',
            (
                'features = ["navigation.instant", "content.action.edit", '
                '"content.action.view"]'
            ),
        )
        config.write_text(text)
    settings = load_settings(config)
    builder.build(settings)
    site = config.parent / "site"
    full = {
        path.relative_to(site): path.read_bytes()
        for path in site.rglob("*")
        if path.is_file()
    }

    # Rebuilding some languages, repeatedly, gives the same site
    for only in (["en"], ["pt"], ["pt"], ["en", "pt"]):
        builder.build(settings, only=only)
        partial = {
            path.relative_to(site): path.read_bytes()
            for path in site.rglob("*")
            if path.is_file()
        }
        assert partial.keys() == full.keys()
        changed = [str(path) for path in full if partial[path] != full[path]]
        assert changed == [], only


def test_warnings_are_printed_once(
    project: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    text = project.read_text().replace('docs_structure = "folder"\n', "")
    project.write_text(text)
    builder.build(load_settings(project))
    output = capsys.readouterr().out
    assert output.count("looks like the folder structure") == 1
