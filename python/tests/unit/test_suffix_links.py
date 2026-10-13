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

from zensical_i18n.extensions.suffix import SuffixLinksExtension

# ----------------------------------------------------------------------------
# Tests
# ----------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("source", "expected"),
    [
        ("[x](guide/page.pt.md)", 'href="guide/page.md"'),
        ("[x](page.en.md#anchor)", 'href="page.md#anchor"'),
        ("[x](page.pt.md?a=1)", 'href="page.md?a=1"'),
        ("![x](assets/logo.pt.png)", 'src="assets/logo.png"'),
        ("[x](app.min.js)", 'href="app.min.js"'),
        ("[x](page.de.md)", 'href="page.de.md"'),
        ("[x](https://example.com/page.pt.md)", "https://example.com/page.pt"),
        ("[x](#section)", 'href="#section"'),
    ],
)
def test_resolve(source: str, expected: str) -> None:
    md = Markdown(extensions=[SuffixLinksExtension(locales=["en", "pt"])])
    assert expected in md.convert(source)


def test_invalid_options() -> None:
    with pytest.raises(ValueError, match="Unknown"):
        SuffixLinksExtension(unknown=True)
    with pytest.raises(TypeError):
        SuffixLinksExtension(locales="pt")
