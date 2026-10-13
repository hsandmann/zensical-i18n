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

from zensical_i18n import languages, nav

# ----------------------------------------------------------------------------
# Tests
# ----------------------------------------------------------------------------


def test_translate_nav() -> None:
    items = [
        "index.md",
        {"Home": "index.md"},
        {"Guide": [{"Install": "guide/install.md"}, "guide/other.md"]},
        {"GitHub": "https://github.com"},
    ]
    assert nav.translate(
        items, {"Home": "Início", "Install": "Instalação"}
    ) == [
        "index.md",
        {"Início": "index.md"},
        {"Guide": [{"Instalação": "guide/install.md"}, "guide/other.md"]},
        {"GitHub": "https://github.com"},
    ]


def test_translate_nav_without_translations() -> None:
    items = [{"Home": "index.md"}]
    assert nav.translate(items, {}) is items


def test_notice() -> None:
    assert languages.notice("pt-BR", "English").endswith("em English.")
    assert languages.notice("pt-PT", "English").startswith("Esta página")
    assert languages.notice("xx", "English").startswith("This page")
    assert languages.notice("pt", "English", "{language}!") == "English!"
