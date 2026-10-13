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
