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
from xml.etree import ElementTree

from bs4 import BeautifulSoup

from zensical_i18n import builder, discovery
from zensical_i18n.settings import load_settings

if TYPE_CHECKING:
    from pathlib import Path

# ----------------------------------------------------------------------------
# Constants
# ----------------------------------------------------------------------------

# Namespaces of sitemaps.
NS = {"s": discovery.SITEMAP_NS, "x": discovery.XHTML_NS}

# Site URL of the fixture project.
BASE = "https://example.com/docs/"

# ----------------------------------------------------------------------------
# Helpers
# ----------------------------------------------------------------------------


def _sitemap(path: Path) -> dict[str, dict[str, str]]:
    """Return the URLs of a sitemap with their alternates."""
    root = ElementTree.parse(path).getroot()  # noqa: S314
    return {
        url.findtext("s:loc", "", NS): {
            link.get("hreflang", ""): link.get("href", "")
            for link in url.findall("x:link", NS)
        }
        for url in root.findall("s:url", NS)
    }


def _head(path: Path) -> list[dict[str, str]]:
    """Return the canonical and alternate links in the head of a page."""
    soup = BeautifulSoup(path.read_text(), "html.parser")
    return [
        {key: str(value) for key, value in link.attrs.items() if key != "rel"}
        | {"rel": " ".join(link["rel"])}
        for link in soup.select("head link[rel=canonical], head link[hreflang]")
    ]


# ----------------------------------------------------------------------------
# Tests
# ----------------------------------------------------------------------------


def test_sitemap_alternates(project: Path) -> None:
    builder.build(load_settings(project))
    site = project.parent / "site"

    # Translated pages declare all translations and the default language
    alternates = {"en": BASE, "pt": f"{BASE}pt/", "x-default": BASE}
    assert _sitemap(site / "sitemap.xml")[BASE] == alternates
    assert _sitemap(site / "pt/sitemap.xml")[f"{BASE}pt/"] == alternates

    # Pages without translations have no alternates, and pages falling back
    # to the default language are left out
    assert _sitemap(site / "sitemap.xml")[f"{BASE}guide/install/"] == {}
    assert f"{BASE}pt/guide/install/" not in _sitemap(site / "pt/sitemap.xml")
    assert _sitemap(site / "pt/sitemap.xml")[f"{BASE}pt/extra/"] == {}


def test_head_links(project: Path) -> None:
    builder.build(load_settings(project))
    site = project.parent / "site"

    # Links to the home pages of all languages are removed
    assert _head(site / "pt/index.html") == [
        {"rel": "canonical", "href": f"{BASE}pt/"}
    ]

    # Pages falling back to the default language point to the original
    assert _head(site / "pt/guide/install/index.html") == [
        {"rel": "canonical", "href": f"{BASE}guide/install/"}
    ]


def test_idempotent(project: Path) -> None:
    settings = load_settings(project)
    builder.build(settings)
    site = project.parent / "site"
    sitemap = (site / "sitemap.xml").read_text()
    page = (site / "pt/guide/install/index.html").read_text()

    # Building only some languages processes all languages again
    builder.build(settings, only=["pt"])
    assert (site / "sitemap.xml").read_text() == sitemap
    assert (site / "pt/guide/install/index.html").read_text() == page


def test_llmstxt(project: Path) -> None:
    config = project.read_text().replace(
        "[project.plugins.i18n]",
        '[project.plugins.llmstxt]\nmarkdown_description = "Docs"\n\n'
        "[project.plugins.i18n]",
    )
    project.write_text(config)
    settings = load_settings(project)
    builder.build(settings)
    builder.build(settings, only=["pt"])
    site = project.parent / "site"

    en = (site / "llms.txt").read_text()
    assert en.count("## Languages") == 1
    assert f"- [Português]({BASE}pt/llms.txt): Documentação (pt)" in en
    pt = (site / "pt/llms.txt").read_text()
    assert f"- [English]({BASE}llms.txt): Docs (en)" in pt


def test_without_site_url(project: Path) -> None:
    config = project.read_text().replace(f'site_url = "{BASE}"\n', "")
    project.write_text(config)
    builder.build(load_settings(project))
    site = project.parent / "site"
    assert "xhtml:link" not in (site / "sitemap.xml").read_text()
