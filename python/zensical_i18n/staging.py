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
import shutil
from pathlib import Path, PurePosixPath
from typing import TYPE_CHECKING, NamedTuple

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
        return mark_fallback(self.path.read_text("utf-8"), self.fallback)


# ----------------------------------------------------------------------------
# Functions
# ----------------------------------------------------------------------------


def collect(settings: Settings, language: Language) -> dict[Path, Source]:
    """Collect the files of a language's staged docs folder.

    The staged folder is the union of three layers, with later layers taking
    precedence: shared files outside of any locale folder, the files of the
    default language (if falling back to it), and the language's own files.
    Each locale folder is thus treated as the docs root.
    """
    docs_dir = settings.docs_dir
    if not docs_dir.is_dir():
        raise I18nError(f"Docs directory does not exist: {docs_dir}")

    # Collect shared files, which are outside of all locale folders
    locales = {lang.locale for lang in settings.languages}
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


def manifest(settings: Settings) -> bytes:
    """Generate the manifest of the pages of all languages.

    The language selector uses the manifest to link to the current page in
    other languages, falling back to their home pages if it doesn't exist.
    """
    pages = {
        lang.locale: page_urls(collect(settings, lang), settings.directory_urls)
        for lang in settings.built
    }
    return json.dumps({"pages": pages}, ensure_ascii=False).encode()


def page_urls(files: dict[Path, Source], directory_urls: bool) -> list[str]:
    """Return the URLs of pages, relative to the language root."""
    urls = set()
    for rel in files:
        if rel.suffix != ".md":
            continue

        # Index pages are rendered to the folder they're contained in
        path = PurePosixPath(*rel.parts).with_suffix("")
        if path.name in ("index", "README"):
            parent = path.parent
            if not directory_urls:
                urls.add(str(parent / "index.html"))
            elif parent.name:
                urls.add(f"{parent}/")
            else:
                urls.add("")
        elif directory_urls:
            urls.add(f"{path}/")
        else:
            urls.add(f"{path}.html")

    # Return sorted URLs
    return sorted(urls)


def mark_fallback(text: str, locale: str) -> bytes:
    """Add the fallback marker to the front matter of a page."""
    line = f"{FALLBACK_KEY}: {locale}\n"
    if text.startswith(("---\n", "---\r\n")):
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

    # Remove files that aren't part of the staged folder anymore
    for path in list(_walk(dest)):
        if path.relative_to(dest) not in files:
            path.unlink()
            changed = True

    # Write generated content, or copy files that changed
    for rel, source in files.items():
        target = dest / rel
        content = source.content()
        if content is not None:
            if target.is_file() and target.read_bytes() == content:
                continue
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(content)
        elif source.path is not None:
            if _same_stat(source.path, target):
                continue
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source.path, target)
        changed = True

    # Remove empty folders, and return whether anything changed
    _remove_empty_dirs(dest)
    return changed


# ----------------------------------------------------------------------------


def _same_stat(src: Path, target: Path) -> bool:
    """Check whether two files have the same size and modification time."""
    try:
        a, b = src.stat(), target.stat()
    except FileNotFoundError:
        return False
    return a.st_size == b.st_size and int(a.st_mtime) == int(b.st_mtime)


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
