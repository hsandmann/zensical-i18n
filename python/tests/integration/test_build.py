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

import pytest
from bs4 import BeautifulSoup, Tag

from zensical_i18n import builder
from zensical_i18n.settings import load_settings

if TYPE_CHECKING:
    from pathlib import Path

# ----------------------------------------------------------------------------
# Helpers
# ----------------------------------------------------------------------------


def _page(site: Path, path: str) -> BeautifulSoup:
    """Parse a page of the built site."""
    return BeautifulSoup(site.joinpath(path).read_text(), "html.parser")


def _title(soup: BeautifulSoup) -> str:
    """Return the title of a page."""
    assert soup.title is not None
    return soup.title.get_text()


def _lang(soup: BeautifulSoup) -> str:
    """Return the language of a page."""
    assert soup.html is not None
    return str(soup.html["lang"])


def _select(soup: BeautifulSoup, selector: str) -> Tag:
    """Return the element matching the selector, which must exist."""
    element = soup.select_one(selector)
    assert element is not None
    return element


def _nav(soup: BeautifulSoup) -> list[str]:
    """Return the titles of the primary navigation."""
    links = soup.select(".md-sidebar--primary .md-nav__link")
    return [" ".join(link.get_text().split()) for link in links]


# ----------------------------------------------------------------------------
# Fixtures
# ----------------------------------------------------------------------------


@pytest.fixture
def site(project: Path) -> Path:
    """Build the fixture project and return the site folder."""
    builder.build(load_settings(project))
    return project.parent / "site"


# ----------------------------------------------------------------------------
# Tests
# ----------------------------------------------------------------------------


def test_structure(site: Path) -> None:
    for path in [
        "index.html",
        "guide/install/index.html",
        "zensical-i18n.json",
        "pt/index.html",
        "pt/guide/install/index.html",
        "pt/extra/index.html",
        "pt/assets/logo.svg",
        "pt/zensical-i18n.json",
    ]:
        assert site.joinpath(path).is_file(), path
    assert not site.joinpath("extra").exists()


def test_languages(site: Path) -> None:
    en = _page(site, "index.html")
    assert _lang(en) == "en"
    assert _title(en).endswith("- Docs")

    pt = _page(site, "pt/index.html")
    assert _lang(pt) == "pt"
    assert _title(pt) == "Início - Documentação"
    assert "Início" in _nav(pt)
    assert "Instalação" in " ".join(_nav(pt))


def test_selector(site: Path) -> None:
    soup = _page(site, "pt/guide/install/index.html")
    selector = _select(soup, "[data-md-i18n]")
    assert selector["data-md-i18n-base"] == "../../"
    assert selector["data-md-i18n-manifest"] == "../../zensical-i18n.json"
    links = {a["hreflang"]: a for a in selector.select("a[data-md-i18n-root]")}
    assert links["en"]["data-md-i18n-root"] == "../"
    assert links["pt"]["data-md-i18n-root"] == "./"
    assert links["pt"].has_attr("aria-current")
    assert not links["en"].has_attr("aria-current")


def test_notice(site: Path) -> None:
    fallback = _page(site, "pt/guide/install/index.html")
    notice = _select(fallback, ".md-i18n-notice")
    assert "English" in notice.get_text()

    # Translated pages and the default language don't show a notice
    assert _page(site, "pt/index.html").select_one(".md-i18n-notice") is None
    assert _page(site, "index.html").select_one(".md-i18n-notice") is None


def test_manifest(site: Path) -> None:
    manifest = json.loads(site.joinpath("zensical-i18n.json").read_text())
    assert manifest["pages"] == {
        "en": ["", "guide/install/"],
        "pt": ["", "extra/", "guide/install/"],
    }


def test_site_url(site: Path) -> None:
    sitemap = site.joinpath("pt/sitemap.xml").read_text()
    assert "https://example.com/docs/pt/extra/" in sitemap


def test_rebuild(project: Path, site: Path) -> None:
    settings = load_settings(project)

    # Rebuilding renders all languages again, each with its own cache
    builder.build(settings)
    assert _title(_page(site, "pt/index.html")).startswith("Início")
    assert not project.parent.joinpath(".cache").exists()

    # Changes to translations are picked up
    page = project.parent / "docs/pt/index.md"
    page.write_text(page.read_text() + "\nAtualizado.\n")
    builder.build(settings, only=["pt"])
    assert "Atualizado." in site.joinpath("pt/index.html").read_text()
    assert site.joinpath("index.html").is_file()


def test_project_cache_is_restored(project: Path) -> None:
    cache = project.parent / ".cache"
    cache.mkdir()
    cache.joinpath("marker").write_text("project")
    builder.build(load_settings(project))
    assert cache.joinpath("marker").read_text() == "project"


# Module of Zensical's emoji extension, referenced with YAML tags.
EMOJI = "zensical.extensions.emoji"


def test_mkdocs_yaml(project: Path) -> None:
    root = project.parent
    project.unlink()
    config = root / "mkdocs.yml"
    config.write_text(
        "site_name: Docs\n"
        "markdown_extensions:\n"
        "  - pymdownx.emoji:\n"
        f"      emoji_index: !!python/name:{EMOJI}.twemoji\n"
        f"      emoji_generator: !!python/name:{EMOJI}.to_svg\n"
        "plugins:\n"
        "  - search\n"
        "  - i18n:\n"
        "      languages:\n"
        "        - locale: en\n"
        "          name: English\n"
        "          default: true\n"
        "        - locale: pt\n"
        "          name: Português\n"
        "          site_name: Documentação\n"
    )
    builder.build(load_settings(config))
    pt = _page(root / "site", "pt/index.html")
    assert _lang(pt) == "pt"
    assert _title(pt) == "Início - Documentação"


def test_admonitions(site: Path) -> None:
    def titles(path: str) -> list[str]:
        soup = _page(site, path)
        return [p.get_text() for p in soup.select(".admonition-title")]

    # Default titles are translated, explicit titles are kept, also on pages
    # that fall back to the default language
    assert titles("pt/index.html") == ["Nota"]
    assert titles("pt/guide/install/index.html") == ["Nota", "Custom tip"]
    assert titles("guide/install/index.html") == ["Note", "Custom tip"]


def test_selector_links_to_translations(site: Path) -> None:
    soup = _page(site, "pt/guide/install/index.html")
    links = {
        str(a["hreflang"]): str(a["href"])
        for a in soup.select("a[data-md-i18n-root]")
    }
    assert links["en"] == "../../../guide/install/"


def test_fallback_content_language(site: Path) -> None:
    article = _select(_page(site, "pt/guide/install/index.html"), "article")
    assert article["lang"] == "en"
    assert article["dir"] == "ltr"

    # The notice is in the language of the site
    notice = _select(_page(site, "pt/guide/install/index.html"), "aside")
    assert notice["lang"] == "pt"

    # Translated pages aren't marked
    article = _select(_page(site, "pt/index.html"), "article")
    assert not article.has_attr("lang")
