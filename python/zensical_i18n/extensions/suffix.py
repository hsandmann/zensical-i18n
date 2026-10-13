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

from pathlib import PurePosixPath
from typing import TYPE_CHECKING, Any
from urllib.parse import urlsplit, urlunsplit

from markdown import Extension, Markdown
from markdown.treeprocessors import Treeprocessor

if TYPE_CHECKING:
    from xml.etree.ElementTree import Element

# ----------------------------------------------------------------------------
# Constants
# ----------------------------------------------------------------------------

# Attributes of elements that reference files.
ATTRIBUTES = {"a": "href", "img": "src", "source": "src"}

# ----------------------------------------------------------------------------
# Classes
# ----------------------------------------------------------------------------


class SuffixLinksTreeprocessor(Treeprocessor):
    """Resolve links to files with a locale suffix.

    With the suffix structure, `page.pt.md` and `logo.pt.png` are staged as
    `page.md` and `logo.png`, so links to them, which mkdocs-static-i18n
    resolves, would break. We remove the suffix, so Zensical resolves links
    to the file of the language being built.
    """

    name = "zensical_i18n.suffix"

    def __init__(self, md: Markdown, locales: list[str]):
        super().__init__(md)
        self.locales = set(locales)

    def run(self, root: Element) -> None:
        for el in root.iter():
            attribute = ATTRIBUTES.get(el.tag)
            value = el.get(attribute) if attribute else None
            if attribute and value:
                el.set(attribute, self._resolve(value))

    def _resolve(self, url: str) -> str:
        """Remove the locale suffix from a relative URL, if any."""
        parts = urlsplit(url)
        if parts.scheme or parts.netloc or not parts.path:
            return url
        path = PurePosixPath(parts.path)
        names = path.name.split(".")
        if len(names) < 3 or not names[0] or names[-2] not in self.locales:  # noqa: PLR2004
            return url
        name = ".".join([*names[:-2], names[-1]])
        return urlunsplit(parts._replace(path=str(path.with_name(name))))


# ----------------------------------------------------------------------------


class SuffixLinksExtension(Extension):
    """Resolve links to files with a locale suffix."""

    name = "zensical_i18n.extensions.suffix"

    def __init__(self, **kwargs: Any) -> None:
        locales = kwargs.pop("locales", [])
        if kwargs:
            raise ValueError(
                f"Unknown suffix options: {', '.join(sorted(kwargs))}"
            )
        if not isinstance(locales, list):
            raise TypeError("Suffix locales must be a list")
        self.locales = [str(locale) for locale in locales]

    def extendMarkdown(self, md: Markdown) -> None:
        if not self.locales:
            return
        md.registerExtension(self)

        # Inline processing runs at 20, creating links and images, and
        # Zensical resolves links at 0, so we run in between
        tree = SuffixLinksTreeprocessor(md, self.locales)
        md.treeprocessors.register(tree, tree.name, 1)


# ----------------------------------------------------------------------------
# Functions
# ----------------------------------------------------------------------------


def makeExtension(**kwargs: Any) -> SuffixLinksExtension:
    """Register the suffix links Markdown extension."""
    return SuffixLinksExtension(**kwargs)
