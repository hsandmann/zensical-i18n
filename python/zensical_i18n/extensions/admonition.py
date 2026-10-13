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

from typing import TYPE_CHECKING, Any

from markdown import Extension, Markdown
from markdown.treeprocessors import Treeprocessor

if TYPE_CHECKING:
    from collections.abc import Sequence
    from xml.etree.ElementTree import Element

# ----------------------------------------------------------------------------
# Classes
# ----------------------------------------------------------------------------


class AdmonitionTranslationsTreeprocessor(Treeprocessor):
    """Translate default titles of admonitions and collapsible blocks.

    Admonitions without an explicit title get one derived from their type,
    e.g., `Note` for `note`, which we replace with its translation. Explicit
    titles are left untouched, as are admonitions without a title. This works
    for all syntaxes, i.e., `!!!`, `???` and `///` blocks, as they all render
    to the same structure.
    """

    name = "zensical_i18n.admonition"

    def __init__(self, md: Markdown, translations: dict[str, str]):
        super().__init__(md)
        self.translations = translations

    def run(self, root: Element) -> None:
        for el in root.iter():
            classes = (el.get("class") or "").split()

            # Admonitions render to a div with a title paragraph
            if el.tag == "div" and "admonition" in classes and len(el):
                types = [name for name in classes if name != "admonition"]
                title = el[0]
                if title.tag == "p" and "admonition-title" in (
                    title.get("class") or ""
                ):
                    self._translate(title, types)

            # Collapsible blocks render to details with a summary
            elif el.tag == "details" and len(el) and el[0].tag == "summary":
                self._translate(el[0], classes)

    def _translate(self, title: Element, types: Sequence[str]) -> None:
        """Translate the title, if it's the default title for the type."""
        if not types or len(title) or not title.text:
            return
        kind = types[0]
        if kind not in self.translations:
            return
        if title.text.strip() in (kind.capitalize(), kind.title()):
            title.text = self.translations[kind]


# ----------------------------------------------------------------------------


class AdmonitionTranslationsExtension(Extension):
    """Translate default titles of admonitions."""

    name = "zensical_i18n.extensions.admonition"

    def __init__(self, **kwargs: Any) -> None:
        translations = kwargs.pop("translations", {})
        if kwargs:
            raise ValueError(
                f"Unknown admonition options: {', '.join(sorted(kwargs))}"
            )
        if not isinstance(translations, dict):
            raise TypeError("Admonition translations must be a mapping")
        self.translations = {
            str(kind): str(title) for kind, title in translations.items()
        }

    def extendMarkdown(self, md: Markdown) -> None:
        if not self.translations:
            return
        md.registerExtension(self)

        # Inline processing runs at 20, prettifying at 10 - titles are final
        # after inline processing, and plain text is escaped on serialization
        tree = AdmonitionTranslationsTreeprocessor(md, self.translations)
        md.treeprocessors.register(tree, tree.name, 15)


# ----------------------------------------------------------------------------
# Functions
# ----------------------------------------------------------------------------


def makeExtension(**kwargs: Any) -> AdmonitionTranslationsExtension:
    """Register the admonition translations Markdown extension."""
    return AdmonitionTranslationsExtension(**kwargs)
