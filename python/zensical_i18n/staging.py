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
import os
import re
import shutil
from pathlib import Path, PurePosixPath
from typing import TYPE_CHECKING, NamedTuple
from urllib.parse import quote

from zensical_i18n.settings import I18nError, Language, Settings

if TYPE_CHECKING:
    from collections.abc import Iterator

# ----------------------------------------------------------------------------
# Constants
# ----------------------------------------------------------------------------

# Front matter key marking pages that fall back to the default language.
FALLBACK_KEY = "i18n_fallback"

# Manifest of the pages of each language, written to each language's root.
MANIFEST = "zensical-i18n.json"

# Front matter at the start of a page, which must be closed to be one.
FRONT_MATTER = re.compile(
    r"\A---[ \t]*\r?\n(?:.*?\r?\n)?(?:---|\.\.\.)[ \t]*\r?$",
    re.DOTALL | re.MULTILINE,
)

# Byte order mark, which editors on Windows may add to the start of files.
BOM = "\ufeff"

# Two-letter language codes of ISO 639-1, to recognize suffixes of locales.
LANGUAGE_CODES = frozenset(
    (
        "aa",
        "ab",
        "ae",
        "af",
        "ak",
        "am",
        "an",
        "ar",
        "as",
        "av",
        "ay",
        "az",
        "ba",
        "be",
        "bg",
        "bh",
        "bi",
        "bm",
        "bn",
        "bo",
        "br",
        "bs",
        "ca",
        "ce",
        "ch",
        "co",
        "cr",
        "cs",
        "cu",
        "cv",
        "cy",
        "da",
        "de",
        "dv",
        "dz",
        "ee",
        "el",
        "en",
        "eo",
        "es",
        "et",
        "eu",
        "fa",
        "ff",
        "fi",
        "fj",
        "fo",
        "fr",
        "fy",
        "ga",
        "gd",
        "gl",
        "gn",
        "gu",
        "gv",
        "ha",
        "he",
        "hi",
        "ho",
        "hr",
        "ht",
        "hu",
        "hy",
        "hz",
        "ia",
        "id",
        "ie",
        "ig",
        "ii",
        "ik",
        "io",
        "is",
        "it",
        "iu",
        "ja",
        "jv",
        "ka",
        "kg",
        "ki",
        "kj",
        "kk",
        "kl",
        "km",
        "kn",
        "ko",
        "kr",
        "ks",
        "ku",
        "kv",
        "kw",
        "ky",
        "la",
        "lb",
        "lg",
        "li",
        "ln",
        "lo",
        "lt",
        "lu",
        "lv",
        "mg",
        "mh",
        "mi",
        "mk",
        "ml",
        "mn",
        "mr",
        "ms",
        "mt",
        "my",
        "na",
        "nb",
        "nd",
        "ne",
        "ng",
        "nl",
        "nn",
        "no",
        "nr",
        "nv",
        "ny",
        "oc",
        "oj",
        "om",
        "or",
        "os",
        "pa",
        "pi",
        "pl",
        "ps",
        "pt",
        "qu",
        "rm",
        "rn",
        "ro",
        "ru",
        "rw",
        "sa",
        "sc",
        "sd",
        "se",
        "sg",
        "si",
        "sk",
        "sl",
        "sm",
        "sn",
        "so",
        "sq",
        "sr",
        "ss",
        "st",
        "su",
        "sv",
        "sw",
        "ta",
        "te",
        "tg",
        "th",
        "ti",
        "tk",
        "tl",
        "tn",
        "to",
        "tr",
        "ts",
        "tt",
        "tw",
        "ty",
        "ug",
        "uk",
        "ur",
        "uz",
        "ve",
        "vi",
        "vo",
        "wa",
        "wo",
        "xh",
        "yi",
        "yo",
        "za",
        "zh",
        "zu",
    )
)

# ----------------------------------------------------------------------------
# Classes
# ----------------------------------------------------------------------------


class Source(NamedTuple):
    """A file of a staged docs folder."""

    path: Path | None = None
    fallback: str | None = None
    data: bytes | None = None

    def content(self) -> bytes | None:
        """Return generated content, or nothing if copied verbatim."""
        if self.data is not None:
            return self.data
        if self.fallback is None or self.path is None:
            return None
        if self.path.suffix != ".md":
            return None
        try:
            text = self.path.read_text("utf-8")
        except UnicodeDecodeError:
            return None  # Zensical will report the encoding
        return mark_fallback(text, self.fallback)


class Page(NamedTuple):
    """A page of a language."""

    src: str  # path in the staged docs folder, e.g., `guide/index.md`
    translated: bool
    source: str = ""  # path in the docs folder, e.g., `guide/index.pt.md`


# ----------------------------------------------------------------------------
# Functions
# ----------------------------------------------------------------------------


def collect(settings: Settings, language: Language) -> dict[Path, Source]:
    """Collect the files of a language's staged docs folder.

    Depending on the docs structure, translations are files with the locale
    as a suffix, e.g., `page.pt.md`, or files in a folder named after the
    locale, e.g., `pt/page.md`. Pages missing in a language are taken from
    the default language, if falling back to it, and marked as fallbacks.
    """
    docs_dir = settings.docs_dir
    if not docs_dir.is_dir():
        raise I18nError(f"Docs directory does not exist: {docs_dir}")
    if settings.docs_structure == "folder":
        files = _collect_folder(settings, language)
    else:
        files = _collect_suffix(settings, language)
    return _drop_shadowed(files, settings.directory_urls)


def check(settings: Settings) -> list[str]:
    """Check the sources for likely mistakes, returning warnings.

    With the suffix structure, pages suffixed with something that looks like
    a locale, which isn't configured, are built as pages of their own, e.g.,
    `index.de.md` as `/index.de/`, which happens after removing a language.
    """
    warnings = []
    if settings.docs_structure == "suffix" and settings.docs_dir.is_dir():
        locales = {lang.locale for lang in settings.languages}
        for path in _walk(settings.docs_dir):
            parts = path.name.split(".")
            primary = re.split(r"[_-]", parts[-2])[0] if len(parts) > 2 else ""  # noqa: PLR2004
            if (
                path.suffix == ".md"
                and primary in LANGUAGE_CODES
                and parts[-2] not in locales
            ):
                rel = path.relative_to(settings.docs_dir)
                warnings.append(
                    f"{rel} has the suffix '{parts[-2]}', which isn't a "
                    "configured locale, so it's built as a page of its own."
                )
    return warnings


def split_suffix(rel: Path, locales: set[str]) -> tuple[Path, str | None]:
    """Split the locale suffix off a file name, e.g., `page.pt.md`.

    Only configured locales are suffixes, so names like `app.min.js` are left
    untouched. Returns the path without suffix, and the locale, if any.
    """
    parts = rel.name.split(".")
    if len(parts) >= 3 and parts[0] and parts[-2] in locales:  # noqa: PLR2004
        name = ".".join([*parts[:-2], parts[-1]])
        return rel.with_name(name), parts[-2]
    return rel, None


def _collect_folder(
    settings: Settings, language: Language
) -> dict[Path, Source]:
    """Collect files of a language with the folder structure.

    The staged folder is the union of three layers, with later layers taking
    precedence: shared files outside of any locale folder, the files of the
    default language (if falling back to it), and the language's own files.
    Each locale folder is thus treated as the docs root.
    """
    docs_dir = settings.docs_dir

    # Ensure locale folders match locales exactly, or they'd be shared files
    # on case-sensitive file systems, and clash on case-insensitive ones
    locales = {lang.locale for lang in settings.languages}
    folded = {locale.casefold(): locale for locale in locales}
    for entry in docs_dir.iterdir():
        locale = folded.get(entry.name.casefold())
        if locale and entry.name != locale:
            raise I18nError(
                f"Folder {entry} must be named '{locale}' like its locale."
            )

    # Collect shared files, which are outside of all locale folders
    files: dict[Path, Source] = {}
    for path in _walk(docs_dir):
        rel = path.relative_to(docs_dir)
        if rel.parts[0] not in locales:
            files[rel] = Source(path)

    # Collect files of the default language first, if falling back to it
    layers = [language.locale]
    if settings.fallback_to_default and not language.default:
        layers.insert(0, settings.default.locale)

    # Collect files of each layer, marking those that are fallbacks
    for locale in layers:
        locale_dir = docs_dir / locale
        if not locale_dir.is_dir():
            if language.default:
                raise I18nError(f"Docs directory does not exist: {locale_dir}")
            continue
        fallback = None if locale == language.locale else locale
        for path in _walk(locale_dir):
            files[path.relative_to(locale_dir)] = Source(path, fallback)

    # Return collected files
    return files


def _collect_suffix(
    settings: Settings, language: Language
) -> dict[Path, Source]:
    """Collect files of a language with the suffix structure.

    Files without suffix belong to the default language, and files suffixed
    with a locale are its translations, e.g., `page.pt.md` for `page.md`. A
    language gets its own files, then those suffixed with the default locale,
    then those without suffix, like in mkdocs-static-i18n. Pages of the default
    language are fallbacks in other languages, while other files, e.g., images,
    are shared by all languages.
    """
    docs_dir = settings.docs_dir
    locales = {lang.locale for lang in settings.languages}
    default = settings.default.locale

    # Group files by their path without suffix
    variants: dict[Path, dict[str | None, Path]] = {}
    for path in _walk(docs_dir):
        rel, locale = split_suffix(path.relative_to(docs_dir), locales)
        variants.setdefault(rel, {})[locale] = path

    # Pick the variant of each file for the language, ensuring the default
    # language doesn't have two variants, like mkdocs-static-i18n does
    files: dict[Path, Source] = {}
    for rel, paths in sorted(variants.items()):
        if default in paths and None in paths:
            raise I18nError(
                f"Conflicting files for the default language: {paths[None]} "
                f"and {paths[default]}. Remove one of them."
            )
        if language.locale in paths:
            files[rel] = Source(paths[language.locale])
            continue

        # Use the default language's variant, which is a fallback for pages
        path = paths.get(default) or paths.get(None)
        if path is None:
            continue
        if language.default or rel.suffix != ".md":
            files[rel] = Source(path)
        elif settings.fallback_to_default:
            files[rel] = Source(path, default)

    # Return collected files
    return files


def _drop_shadowed(
    files: dict[Path, Source], directory_urls: bool
) -> dict[Path, Source]:
    """Drop fallback pages rendered to the same URL as translated ones.

    A translated `README.md` and a fallback `index.md` in the same folder are
    rendered to the same URL, where Zensical prefers `index.md`, which would
    hide the translation.
    """
    translated = {
        page_url(rel, directory_urls)
        for rel, source in files.items()
        if rel.suffix == ".md" and source.fallback is None
    }
    return {
        rel: source
        for rel, source in files.items()
        if source.fallback is None
        or rel.suffix != ".md"
        or page_url(rel, directory_urls) not in translated
    }


def manifest(settings: Settings) -> bytes:
    """Generate the manifest of the pages of all languages.

    The language selector uses the manifest to link to the current page in
    other languages, falling back to their home pages if it doesn't exist.
    """
    data = {
        lang.locale: sorted(pages(settings, lang)) for lang in settings.built
    }
    return json.dumps({"pages": data}, ensure_ascii=False).encode()


def pages(settings: Settings, language: Language) -> dict[str, bool]:
    """Return the pages of a language, and whether they're translated.

    Pages are identified by their URL, relative to the language root. Pages
    that fall back to the default language aren't translated, while shared
    pages, which are outside of all locale folders, are.
    """
    return {
        url: page.translated
        for url, page in page_sources(settings, language).items()
    }


def page_sources(settings: Settings, language: Language) -> dict[str, Page]:
    """Return the pages of a language with their sources, by URL."""
    result: dict[str, Page] = {}
    for rel, source in sorted(collect(settings, language).items()):
        url = page_url(rel, settings.directory_urls)
        if url is None:
            continue
        page = Page(
            PurePosixPath(*rel.parts).as_posix(),
            not source.fallback,
            _source_path(settings, source),
        )
        if url not in result or (
            page.translated and not result[url].translated
        ):
            result[url] = page
    return result


def page_url(rel: Path, directory_urls: bool) -> str | None:
    """Return the URL of a page, relative to the language root."""
    if rel.suffix != ".md":
        return None

    # Index pages are rendered to the folder they're contained in
    path = PurePosixPath(*rel.parts).with_suffix("")
    if path.name in ("index", "README"):
        parent = path.parent
        if not directory_urls:
            return str(parent / "index.html")
        return f"{parent}/" if parent.name else ""

    # Other pages are rendered to a folder or file of the same name
    return f"{path}/" if directory_urls else f"{path}.html"


def url_keys(url: str) -> list[str]:
    """Return the forms of a page URL that Zensical might use in templates.

    Zensical encodes `page.url` like `encode_url`, but keeps `%` and `?` as
    is, so we use all forms, unencoded included, to match it reliably.
    """
    keys = [
        url,
        encode_url(url),
        quote(url, safe="/!$'()*+,;=:@%?").replace("~", "%7E"),
    ]
    return list(dict.fromkeys(keys))


def encode_url(url: str) -> str:
    """Percent-encode a page URL the way Zensical does.

    Zensical keeps the characters that are allowed in URL paths, except for
    `&` and `~`, which allows to compare URLs with `page.url` in templates.
    """
    return quote(url, safe="/!$'()*+,;=:@").replace("~", "%7E")


def page_urls(files: dict[Path, Source], directory_urls: bool) -> list[str]:
    """Return the URLs of pages, relative to the language root."""
    urls = {page_url(rel, directory_urls) for rel in files}
    return sorted(url for url in urls if url is not None)


def mark_fallback(text: str, locale: str) -> bytes:
    """Add the fallback marker to the front matter of a page.

    The marker is added to existing front matter, or as new front matter, if
    the page has none - a leading `---` without a closing one is a rule.
    """
    text = text.removeprefix(BOM)
    line = f"{FALLBACK_KEY}: {locale}\n"
    if FRONT_MATTER.match(text):
        head, _, body = text.partition("\n")
        return f"{head}\n{line}{body}".encode()
    return f"---\n{line}---\n\n{text}".encode()


def sync(files: dict[Path, Source], dest: Path) -> bool:
    """Mirror files into a folder, writing only what changed.

    Unchanged files keep their modification time, so Zensical's watcher and
    cache aren't disturbed. Returns whether anything was written or removed.
    """
    changed = False
    dest.mkdir(parents=True, exist_ok=True)

    # Remove symbolic links, which we never create, so writes can't follow
    # them outside of the folder, and files that aren't staged anymore
    for dirpath, dirnames, filenames in os.walk(dest):
        for name in [*dirnames, *filenames]:
            path = Path(dirpath) / name
            rel = path.relative_to(dest)
            if path.is_symlink() or (name in filenames and rel not in files):
                path.unlink()
                changed = True
        dirnames[:] = [
            name for name in dirnames if (Path(dirpath) / name).is_dir()
        ]

    # Write generated content, or copy files that changed - files may vanish
    # while being synchronized, e.g., temporary files of editors
    for rel, source in files.items():
        target = dest / rel
        try:
            changed |= _write(source, target)
        except FileNotFoundError:
            continue

    # Remove empty folders, and return whether anything changed
    _remove_empty_dirs(dest)
    return changed


# ----------------------------------------------------------------------------


def _write(source: Source, target: Path) -> bool:
    """Write a file, if it changed, returning whether it was written."""
    content = source.content()
    if content is not None:
        if target.is_file() and target.read_bytes() == content:
            return False
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(content)
        return True
    if source.path is None or _same_stat(source.path, target):
        return False
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source.path, target)
    return True


def _source_path(settings: Settings, source: Source) -> str:
    """Return the path of a source in the docs folder."""
    if source.path is None:
        return ""
    rel = source.path.relative_to(settings.docs_dir)
    return PurePosixPath(*rel.parts).as_posix()


def _same_stat(src: Path, target: Path) -> bool:
    """Check whether two files have the same size and modification time.

    Modification times are compared in nanoseconds, which copying preserves,
    so files changed within the same second are detected.
    """
    try:
        a, b = src.stat(), target.stat()
    except FileNotFoundError:
        return False
    return a.st_size == b.st_size and a.st_mtime_ns == b.st_mtime_ns


def _walk(root: Path) -> Iterator[Path]:
    """Walk a folder, yielding files in a stable order."""
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames.sort()
        for name in sorted(filenames):
            yield Path(dirpath) / name


def _remove_empty_dirs(root: Path) -> None:
    """Remove empty folders below the given folder."""
    for dirpath, _, _ in sorted(os.walk(root), reverse=True):
        path = Path(dirpath)
        if path != root and not any(path.iterdir()):
            path.rmdir()
