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

import html
import os
import re
from pathlib import Path, PurePosixPath
from typing import TYPE_CHECKING
from urllib.parse import unquote
from xml.etree import ElementTree

import click

from zensical_i18n import languages, staging

if TYPE_CHECKING:
    from zensical_i18n.settings import Language, Settings

# ----------------------------------------------------------------------------
# Constants
# ----------------------------------------------------------------------------

# Namespaces of sitemaps, and of the links to alternate languages in them.
SITEMAP_NS = "http://www.sitemaps.org/schemas/sitemap/0.9"
XHTML_NS = "http://www.w3.org/1999/xhtml"

# Links to alternate languages the theme adds to the head of every page.
ALTERNATE = re.compile(
    r"[ \t]*<link\b(?=[^>]*\brel=[\"']?alternate\b)(?=[^>]*\bhreflang=)[^>]*>"
    r"\r?\n?"
)

# Canonical link the theme adds to the head of every page.
CANONICAL = re.compile(
    r"(<link\b(?=[^>]*\brel=[\"']?canonical\b)[^>]*\bhref=)"
    r"(\"[^\"]*\"|'[^']*'|[^\s>]+)"
)

# Element containing the content of a page.
ARTICLE = re.compile(r"<article\b[^>]*\bmd-content__inner\b[^>]*>")

# Edit and view links of a page.
ACTION = re.compile(r"<a\b[^>]*\bmd-content__button\b[^>]*>")

# Marker of the section of llms.txt listing the other languages, so we can
# replace it without touching the sections of the project.
LLMS_MARKER = "<!-- zensical-i18n: languages -->"
LLMS_SECTION = "## Languages"

# ----------------------------------------------------------------------------
# Classes
# ----------------------------------------------------------------------------


class Site:
    """The pages of all languages of an assembled site."""

    def __init__(self, settings: Settings):
        self.settings = settings
        site_url = settings.project.get("site_url")
        self.base = str(site_url).rstrip("/") + "/" if site_url else None
        self.languages = [
            lang for lang in settings.built if self.root(lang).is_dir()
        ]
        self.pages = {
            lang.locale: staging.page_sources(settings, lang)
            for lang in self.languages
        }

    def root(self, language: Language) -> Path:
        """Return the folder of a language in the site."""
        return self.settings.site_dir / language.prefix

    def url(self, language: Language, path: str = "") -> str:
        """Return the absolute URL of a page, given its encoded path."""
        prefix = f"{language.prefix}/" if language.prefix else ""
        return f"{self.base}{prefix}{path}"

    def page(
        self, language: Language, path: str, *, encoded: bool = True
    ) -> staging.Page | None:
        """Return a page of a language, given its path.

        Paths in URLs are encoded, while paths of files on disk aren't.
        """
        return self.pages[language.locale].get(
            unquote(path) if encoded else path
        )

    def translated(self, language: Language, path: str) -> bool:
        """Check whether a page is translated, given its encoded path."""
        page = self.page(language, path)
        return page is not None and page.translated

    def alternates(self, language: Language, path: str) -> dict[str, str]:
        """Return the translations of a page by language tag.

        Pages falling back to the default language aren't translations, so
        they're left out. Only pages with at least one translation have
        alternates, in which case the default language is the `x-default`.
        Paths are encoded, so URLs match the ones Zensical generates.
        """
        if not self.translated(language, path):
            return {}
        result = {
            languages.hreflang(lang.locale): self.url(lang, path)
            for lang in self.languages
            if self.translated(lang, path)
        }
        if len(result) < 2:  # noqa: PLR2004
            return {}
        default = self.settings.default
        if self.translated(default, path):
            result["x-default"] = self.url(default, path)
        return result


# ----------------------------------------------------------------------------
# Functions
# ----------------------------------------------------------------------------


def publish(settings: Settings) -> None:
    """Make the assembled site discoverable by search engines and LLMs.

    Translations are declared in the sitemaps of all languages using hreflang
    alternates, which search engines treat like links in the head of pages.
    Pages falling back to the default language are marked with the language
    of their content, and point to the original page as their canonical URL,
    and llms.txt files link to each other. All steps are idempotent, as only
    some languages might have been built.
    """
    site = Site(settings)
    for language in site.languages:
        _process_pages(site, language)
        if site.base:
            _process_sitemap(site, language)
            _process_llmstxt(site, language)

    # Absolute URLs need the site URL
    if not site.base:
        click.echo(
            "Warning: site_url is not set, so translations aren't declared "
            "in sitemaps and llms.txt."
        )


# ----------------------------------------------------------------------------


def _process_pages(site: Site, language: Language) -> None:
    """Process the pages of a language.

    The theme links every page to the home pages of all languages, which
    tells search engines that pages are translations of home pages. As the
    sitemaps declare the actual translations, we remove those links. The
    language selector doesn't depend on them. Only pages rendered from the
    sources are processed, leaving static HTML files untouched.
    """
    root = site.root(language)
    for path in _html_files(site, language):
        page_path = _page_path(path.relative_to(root), site.settings)
        page = site.page(language, page_path, encoded=False)
        if page is None and page_path != "404.html":
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue

        # Remove links to the home pages of all languages
        result = ALTERNATE.sub("", text)
        if page is not None and not page.translated:
            result = _process_fallback(site, language, page, result)
        if result != text:
            path.write_text(result, encoding="utf-8")


def _process_fallback(
    site: Site, language: Language, page: staging.Page, text: str
) -> str:
    """Process a page falling back to the default language.

    The content is marked with the language it's written in, so screen
    readers, crawlers and LLMs handle it correctly, edit links point to the
    sources of the default language, and the canonical URL to the original.
    """
    default = site.settings.default
    tag = languages.hreflang(default.locale)
    attrs = f' lang="{tag}" dir="{languages.direction(default.locale)}"'

    # Mark the content with its language, if not done yet
    def mark(match: re.Match[str]) -> str:
        element = match[0]
        if " lang=" in element:
            return element
        return element[:-1] + attrs + ">"

    text = ARTICLE.sub(mark, text, count=1)

    # Point edit links to the sources of the default language
    sources = {page.src, staging.encode_url(page.src)}

    def edit(match: re.Match[str]) -> str:
        element = match[0]
        for src in sources:
            element = element.replace(
                f"/{language.locale}/{src}", f"/{default.locale}/{src}"
            )
        return element

    text = ACTION.sub(edit, text)

    # Point the canonical URL to the original, reusing Zensical's encoding
    if site.base:
        base, original = site.url(language), site.url(default)

        def canonical(match: re.Match[str]) -> str:
            href = html.unescape(match[2].strip("\"'"))
            if href.startswith(base):
                href = original + href.removeprefix(base)
            return f'{match[1]}"{html.escape(href, quote=True)}"'

        text = CANONICAL.sub(canonical, text, count=1)
    return text


def _process_sitemap(site: Site, language: Language) -> None:
    """Add translations to the sitemap of a language.

    Pages falling back to the default language are kept, as the theme uses
    sitemaps for instant navigation, but get no alternates - their canonical
    URL points to the original. Existing alternates are replaced.
    """
    path = site.root(language) / "sitemap.xml"
    if not path.is_file():
        return

    # Register namespaces, so they are kept as prefixes on serialization
    ElementTree.register_namespace("", SITEMAP_NS)
    ElementTree.register_namespace("xhtml", XHTML_NS)
    try:
        tree = ElementTree.parse(path)  # noqa: S314
    except ElementTree.ParseError:
        click.echo(f"Warning: couldn't parse {path}, skipping.")
        return

    # Replace alternates of all URLs of the language
    base = site.url(language)
    for url in tree.getroot().findall(f"{{{SITEMAP_NS}}}url"):
        loc = url.findtext(f"{{{SITEMAP_NS}}}loc", "").strip()
        if not loc.startswith(base):
            continue
        for link in url.findall(f"{{{XHTML_NS}}}link"):
            url.remove(link)
        page = loc.removeprefix(base)
        for hreflang, href in site.alternates(language, page).items():
            ElementTree.SubElement(
                url,
                f"{{{XHTML_NS}}}link",
                {"rel": "alternate", "hreflang": hreflang, "href": href},
            )

    # Write sitemap
    ElementTree.indent(tree, space="  ")
    tree.write(path, encoding="UTF-8", xml_declaration=True)


def _process_llmstxt(site: Site, language: Language) -> None:
    """Link the llms.txt files of all languages to each other.

    Zensical writes an llms.txt for each language if the llmstxt plugin is
    enabled. We add a section listing the llms.txt of the other languages,
    which is preceded by a marker, so it's replaced on subsequent runs.
    """
    path = site.root(language) / "llms.txt"
    if not path.is_file():
        return

    # Collect links to the llms.txt files of other languages
    links = [
        f"- [{other.name}]({site.url(other, 'llms.txt')}): "
        f"{_site_name(site.settings, other)} "
        f"({languages.hreflang(other.locale)})"
        for other in site.languages
        if other != language and (site.root(other) / "llms.txt").is_file()
    ]

    # Remove our section, if present, and append it
    text = path.read_text(encoding="utf-8")
    text = text.split(f"\n{LLMS_MARKER}\n", 1)[0].rstrip("\n") + "\n"
    if links:
        text += f"\n{LLMS_MARKER}\n{LLMS_SECTION}\n\n" + "\n".join(links)
        text += "\n"
    path.write_text(text, encoding="utf-8")


# ----------------------------------------------------------------------------


def _html_files(site: Site, language: Language) -> list[Path]:
    """Return the HTML files of a language, skipping other languages."""
    root = site.root(language)
    others = {lang.prefix for lang in site.settings.languages if lang.prefix}
    files = []
    for dirpath, dirnames, filenames in os.walk(root):
        if Path(dirpath) == root and language.default:
            dirnames[:] = [name for name in dirnames if name not in others]
        files.extend(
            Path(dirpath) / name for name in filenames if name.endswith(".html")
        )
    return sorted(files)


def _page_path(rel: Path, settings: Settings) -> str:
    """Return the page URL of an HTML file, relative to the language root."""
    path = PurePosixPath(*rel.parts)
    if settings.directory_urls and path.name == "index.html":
        parent = str(path.parent)
        return "" if parent == "." else f"{parent}/"
    return str(path)


def _site_name(settings: Settings, language: Language) -> str:
    """Return the site name in the given language."""
    name = language.overrides.get("site_name", settings.project["site_name"])
    return str(name)
