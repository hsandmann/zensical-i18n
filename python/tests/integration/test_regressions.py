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
from urllib.parse import urljoin
from xml.etree import ElementTree

from bs4 import BeautifulSoup

from zensical_i18n import builder, discovery
from zensical_i18n.settings import load_settings

if TYPE_CHECKING:
    from pathlib import Path

# ----------------------------------------------------------------------------
# Constants
# ----------------------------------------------------------------------------

# Site URL of the fixture project.
BASE = "https://example.com/docs/"

# Namespaces of sitemaps.
NS = {"s": discovery.SITEMAP_NS, "x": discovery.XHTML_NS}

# ----------------------------------------------------------------------------
# Helpers
# ----------------------------------------------------------------------------


def _build(project: Path, *, config: str = "", **pages: str) -> Path:
    """Add settings and pages to the fixture project, and build it."""
    if config:
        project.write_text(project.read_text() + config)
    for path, content in pages.items():
        file = project.parent / "docs" / path.replace("__", "/")
        file.parent.mkdir(parents=True, exist_ok=True)
        file.write_text(content)
    builder.build(load_settings(project))
    return project.parent / "site"


def _soup(path: Path) -> BeautifulSoup:
    return BeautifulSoup(path.read_text(), "html.parser")


def _alternates(sitemap: Path, loc: str) -> dict[str, str]:
    root = ElementTree.parse(sitemap).getroot()  # noqa: S314
    for url in root.findall("s:url", NS):
        if url.findtext("s:loc", "", NS) == loc:
            return {
                str(link.get("hreflang")): str(link.get("href"))
                for link in url.findall("x:link", NS)
            }
    raise AssertionError(loc)


# ----------------------------------------------------------------------------
# Tests
# ----------------------------------------------------------------------------


def test_special_characters_in_paths(project: Path) -> None:
    names = ["with space", "ünï", "c#sharp", 'it\'s "q"']
    pages = {f"en__{name}.md": f"# {name}\n" for name in names}
    pages |= {f"pt__{name}.md": f"# {name}\n" for name in names[:2]}
    site = _build(project, **pages)

    # Translated pages declare their alternates
    loc = f"{BASE}pt/with%20space/"
    assert _alternates(site / "pt/sitemap.xml", loc)["en"] == (
        f"{BASE}with%20space/"
    )
    assert _alternates(site / "sitemap.xml", f"{BASE}%C3%BCn%C3%AF/")["pt"]

    # Fallback pages point to the encoded original, with valid markup
    for name, encoded in [("c#sharp", "c%23sharp"), ('it\'s "q"', None)]:
        soup = _soup(site / "pt" / name / "index.html")
        canonical = soup.select_one("link[rel=canonical]")
        assert canonical is not None
        href = str(canonical["href"])
        assert href.startswith(BASE)
        assert "/pt/" not in href
        assert '"' not in href
        if encoded:
            assert href == f"{BASE}{encoded}/"

    # The language selector links to translations without JavaScript
    soup = _soup(site / "pt/with space/index.html")
    link = soup.select_one("a[data-md-i18n-locale=en]")
    assert link is not None
    assert str(link["href"]) == "../../with%20space/"


def test_edit_links(project: Path) -> None:
    config = project.read_text().replace(
        "[project]\n",
        '[project]\nrepo_url = "https://github.com/o/r"\n'
        'edit_uri = "edit/main/docs/"\n',
        1,
    )
    project.write_text(config)
    config = '\n[project.theme]\nfeatures = ["content.action.edit"]\n'
    config = project.read_text().replace(
        '[project.theme]\nfeatures = ["navigation.instant"]', config.strip()
    )
    project.write_text(config)
    site = _build(project)

    def edit(path: str) -> str:
        link = _soup(site / path).select_one("a[rel=edit]")
        assert link is not None
        return str(link["href"])

    base = "https://github.com/o/r/edit/main/docs"
    assert edit("index.html") == f"{base}/en/index.md"
    assert edit("pt/index.html") == f"{base}/pt/index.md"
    assert edit("pt/guide/install/index.html") == f"{base}/en/guide/install.md"


def test_unbuilt_language_with_link(project: Path) -> None:
    site = _build(
        project,
        config=(
            '\n[[project.plugins.i18n.languages]]\nlocale = "fr"\n'
            'name = "Français"\nbuild = false\n'
            'link = "https://fr.example.com/"\n'
        ),
    )
    assert not (site / "fr").exists()
    soup = _soup(site / "pt/index.html")
    link = soup.select_one("a[data-md-i18n-locale=fr]")
    assert link is not None
    assert str(link["href"]) == "https://fr.example.com/"
    assert 'hreflang="fr"' not in (site / "sitemap.xml").read_text()


def test_unbuilt_language_folder_is_removed(project: Path) -> None:
    site = _build(project)
    assert (site / "pt").is_dir()
    config = project.read_text().replace(
        'name = "Português"', 'name = "Português"\nbuild = false'
    )
    project.write_text(config)
    builder.build(load_settings(project))
    assert not (site / "pt").exists()


def test_regional_locale(project: Path) -> None:
    config = project.read_text().replace('locale = "pt"', 'locale = "fr_CA"')
    project.write_text(config)
    (project.parent / "docs/pt").rename(project.parent / "docs/fr_CA")
    site = _build(project)
    soup = _soup(site / "fr_CA/index.html")
    assert soup.html is not None
    assert soup.html["lang"] == "fr-CA"
    link = soup.select_one("a[data-md-i18n-locale=fr_CA]")
    assert link is not None
    assert link["hreflang"] == "fr-CA"


def test_llmstxt_keeps_project_sections(project: Path) -> None:
    site = _build(
        project,
        config=(
            "\n[project.plugins.llmstxt]\n"
            'markdown_description = "Docs"\n'
            "[project.plugins.llmstxt.sections]\n"
            '"Languages" = ["index.md"]\n'
            '"Guide" = ["guide/install.md"]\n'
        ),
    )
    builder.build(load_settings(project), only=["pt"])
    text = (site / "llms.txt").read_text()
    assert "## Guide" in text
    assert text.count(discovery.LLMS_MARKER) == 1
    assert f"({BASE}pt/llms.txt)" in text


def test_static_html_is_untouched(project: Path) -> None:
    static = project.parent / "docs/assets/report/index.html"
    static.parent.mkdir(parents=True)
    content = '<link rel="alternate" hreflang="x" href="y">Caf\xe9'
    static.write_bytes(content.encode("latin-1"))
    site = _build(project)
    assert (site / "assets/report/index.html").read_bytes() == (
        content.encode("latin-1")
    )


def test_hidden_files_in_site_dir_are_kept(project: Path) -> None:
    site = project.parent / "site"
    site.joinpath(".git").mkdir(parents=True)
    site.joinpath(".nojekyll").write_text("")
    site.joinpath("stale.html").write_text("")
    _build(project)
    assert site.joinpath(".git").is_dir()
    assert site.joinpath(".nojekyll").exists()
    assert not site.joinpath("stale.html").exists()


def test_names_are_escaped(project: Path) -> None:
    payload = '<img src=x onerror="alert(1)">'
    config = project.read_text().replace(
        'name = "Português"',
        f"name = '{payload}'\nuntranslated_notice = '{payload}'",
    )
    project.write_text(config)
    site = _build(project)
    text = (site / "pt/guide/install/index.html").read_text()
    assert payload not in text

    # Both the name in the selector and the notice are escaped
    soup = _soup(site / "pt/guide/install/index.html")
    link = soup.select_one("a[data-md-i18n-locale=pt] .md-i18n__name")
    notice = soup.select_one(".md-i18n-notice p")
    assert link is not None
    assert notice is not None
    assert link.get_text() == payload
    assert notice.get_text() == payload


def test_translations_trigger_rebuild(project: Path) -> None:
    site = _build(project)
    titles = _soup(site / "pt/index.html").select(".admonition-title")
    assert [title.get_text() for title in titles] == ["Nota"]

    # Changing translations must invalidate Zensical's cache
    project.write_text(
        project.read_text()
        + "\n[project.plugins.i18n.languages.admonition_translations]\n"
        + 'note = "Observação"\n'
    )
    builder.build(load_settings(project), only=["pt"])
    titles = _soup(site / "pt/index.html").select(".admonition-title")
    assert [title.get_text() for title in titles] == ["Observação"]


def test_unknown_rtl_locale(project: Path) -> None:
    config = project.read_text().replace('locale = "pt"', 'locale = "ckb"')
    project.write_text(config)
    (project.parent / "docs/pt").rename(project.parent / "docs/ckb")
    site = _build(project)

    # The theme falls back to English, but language and direction are kept
    soup = _soup(site / "ckb/guide/install/index.html")
    assert soup.html is not None
    assert soup.html["lang"] == "ckb"
    assert soup.body is not None
    assert soup.body["dir"] == "rtl"

    # The notice is in the language of the site, the content isn't
    notice = soup.select_one(".md-i18n-notice")
    article = soup.select_one("article")
    assert notice is not None
    assert article is not None
    assert (notice["lang"], notice["dir"]) == ("ckb", "rtl")
    assert (article["lang"], article["dir"]) == ("en", "ltr")


def test_regional_html_lang(project: Path) -> None:
    config = project.read_text().replace('locale = "pt"', 'locale = "pt_BR"')
    project.write_text(config)
    (project.parent / "docs/pt").rename(project.parent / "docs/pt_BR")
    site = _build(project)
    soup = _soup(site / "pt_BR/index.html")
    assert soup.html is not None
    assert soup.html["lang"] == "pt-BR"


def test_404_without_site_url(project: Path) -> None:
    config = project.read_text().replace(f'site_url = "{BASE}"\n', "")
    project.write_text(config)
    site = _build(project)
    soup = _soup(site / "pt/404.html")
    root = soup.select_one("[data-md-i18n]")
    assert root is not None
    assert root["data-md-i18n-base"] == "/pt/"
    links = {
        str(a["data-md-i18n-locale"]): urljoin("https://x/", str(a["href"]))
        for a in soup.select("a[data-md-i18n-locale]")
    }
    assert links == {"en": "https://x/", "pt": "https://x/pt/"}
