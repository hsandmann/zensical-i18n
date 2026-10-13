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

import pytest
from markdown import Markdown

from zensical_i18n.extensions.admonition import (
    AdmonitionTranslationsExtension,
)

# ----------------------------------------------------------------------------
# Helpers
# ----------------------------------------------------------------------------


def _render(source: str, translations: dict[str, str]) -> str:
    """Render Markdown with admonitions and the translations extension."""
    md = Markdown(
        extensions=[
            "admonition",
            "pymdownx.details",
            "pymdownx.superfences",
            "pymdownx.blocks.admonition",
            "pymdownx.blocks.details",
            AdmonitionTranslationsExtension(translations=translations),
        ]
    )
    return md.convert(source)


# ----------------------------------------------------------------------------
# Tests
# ----------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("source", "expected"),
    [
        ("!!! note\n    Text\n", '<p class="admonition-title">Nota</p>'),
        ("??? note\n    Text\n", "<summary>Nota</summary>"),
        ("???+ note\n    Text\n", "<summary>Nota</summary>"),
        ("/// note\nText\n///\n", '<p class="admonition-title">Nota</p>'),
        ("!!! my-type\n    Text\n", '<p class="admonition-title">Mein</p>'),
    ],
)
def test_default_title(source: str, expected: str) -> None:
    html = _render(source, {"note": "Nota", "my-type": "Mein"})
    assert expected in html


def test_explicit_title() -> None:
    html = _render('!!! note "Custom"\n    Text\n', {"note": "Nota"})
    assert '<p class="admonition-title">Custom</p>' in html


def test_empty_title() -> None:
    html = _render('!!! note ""\n    Text\n', {"note": "Nota"})
    assert "admonition-title" not in html
    assert "Nota" not in html


def test_untranslated_type() -> None:
    html = _render("!!! danger\n    Text\n", {"note": "Nota"})
    assert '<p class="admonition-title">Danger</p>' in html


def test_code_block() -> None:
    html = _render("```\n!!! note\n```\n", {"note": "Nota"})
    assert "!!! note" in html
    assert "Nota" not in html


def test_escaping() -> None:
    html = _render("!!! note\n    Text\n", {"note": "<b>&</b>"})
    assert "&lt;b&gt;&amp;&lt;/b&gt;" in html


def test_invalid_options() -> None:
    with pytest.raises(ValueError, match="Unknown"):
        AdmonitionTranslationsExtension(unknown=True)
    with pytest.raises(TypeError):
        AdmonitionTranslationsExtension(translations=["note"])
