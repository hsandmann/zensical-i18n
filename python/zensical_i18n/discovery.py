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
import re
from pathlib import Path, PurePosixPath
from typing import TYPE_CHECKING
from xml.etree import ElementTree

import click

from zensical_i18n import staging

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

# Section of llms.txt listing the other languages.
LLMS_SECTION = "## Languages"

# ----------------------------------------------------------------------------
# Classes
# ----------------------------------------------------------------------------


class Site:
    """The pages of all languages of an assembled site."""

    def __init__(self, settings: Settings):
        self.settings = settings
        self.base = str(settings.project["site_url"]).rstrip("/") + "/"
        self.languages = [
            lang for lang in settings.built if self.root(lang).is_dir()
        ]
        self.pages = {
            lang.locale: staging.pages(settings, lang)
            for lang in self.languages
        }

    def root(self, language: Language) -> Path:
        """Return the folder of a language in the site."""
        return self.settings.site_dir / language.prefix

    def url(self, language: Language, path: str = "") -> str:
        """Return the absolute URL of a page of a language."""
        prefix = f"{language.prefix}/" if language.prefix else ""
        return f"{self.base}{prefix}{path}"

    def translated(self, language: Language, path: str) -> bool:
        """Check whether a page is translated in the given language."""
        return self.pages[language.locale].get(path, False)

    def alternates(self, language: Language, path: str) -> dict[str, str]:
        """Return the translations of a page, by hreflang code.

        Pages that fall back to the default language aren't translations, so
        they're left out. Only pages with at least one translation have
        alternates, in which case the default language is the `x-default`.
        """
        if not self.translated(language, path):
            return {}
        result = {
            _hreflang(lang.locale): self.url(lang, path)
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
    Pages falling back to the default language point to the original page as
    their canonical URL, and llms.txt files link to each other.
    """
    if not settings.project.get("site_url"):
        click.echo(
            "Warning: site_url is not set, so translations aren't declared "
            "to search engines and LLMs."
        )
        return

    # Process all languages in the site, as pages of one language affect the
    # alternates of the others, even if only some languages were built
    site = Site(settings)
    for language in site.languages:
        _process_pages(site, language)
        _process_sitemap(site, language)
        _process_llmstxt(site, language)


# ----------------------------------------------------------------------------


def _process_pages(site: Site, language: Language) -> None:
    """Remove links to language roots, and fix canonical URLs of fallbacks.

    The theme links every page to the home pages of all languages, which
    tells search engines that pages are translations of home pages. As the
    sitemaps declare the actual translations, we remove those links. The
    language selector doesn't depend on them.
    """
    root = site.root(language)
    for path in _html_files(site, language):
        text = path.read_text(encoding="utf-8")
        result = ALTERNATE.sub("", text)

        # Pages falling back to the default language are copies of the page
        # of the default language, which is thus their canonical URL
        page = _page_path(path.relative_to(root), site.settings)
        if page in site.pages[language.locale] and not site.translated(
            language, page
        ):
            canonical = site.url(site.settings.default, page)
            result = CANONICAL.sub(rf'\g<1>"{canonical}"', result, count=1)

        if result != text:
            path.write_text(result, encoding="utf-8")


def _process_sitemap(site: Site, language: Language) -> None:
    """Add translations to the sitemap of a language.

    Pages falling back to the default language are removed, as their URL is
    not canonical. Existing alternates are replaced, so this is idempotent.
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

    # Process all URLs of the language
    urlset = tree.getroot()
    base = site.url(language)
    for url in list(urlset.findall(f"{{{SITEMAP_NS}}}url")):
        loc = url.findtext(f"{{{SITEMAP_NS}}}loc", "").strip()
        if not loc.startswith(base):
            continue

        # Remove pages falling back to the default language
        page = loc.removeprefix(base)
        if page in site.pages[language.locale] and not site.translated(
            language, page
        ):
            urlset.remove(url)
            continue

        # Replace alternates
        for link in url.findall(f"{{{XHTML_NS}}}link"):
            url.remove(link)
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
    replacing the section if it already exists, so this is idempotent.
    """
    path = site.root(language) / "llms.txt"
    if not path.is_file():
        return

    # Collect links to the llms.txt files of other languages
    links = [
        f"- [{other.name}]({site.url(other, 'llms.txt')}): "
        f"{_site_name(site.settings, other)} ({other.locale})"
        for other in site.languages
        if other != language and (site.root(other) / "llms.txt").is_file()
    ]

    # Remove existing section, which is always the last one, and append
    text = path.read_text(encoding="utf-8")
    text = text.split(f"\n{LLMS_SECTION}\n", 1)[0].rstrip("\n") + "\n"
    if links:
        text += f"\n{LLMS_SECTION}\n\n" + "\n".join(links) + "\n"
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


def _hreflang(locale: str) -> str:
    """Return the hreflang code of a locale, e.g., `pt-BR` for `pt_BR`."""
    return locale.replace("_", "-")
