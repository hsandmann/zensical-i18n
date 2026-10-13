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

from zensical_i18n.builder import admonitions
from zensical_i18n.settings import load_settings

if TYPE_CHECKING:
    from pathlib import Path

# ----------------------------------------------------------------------------
# Tests
# ----------------------------------------------------------------------------


def test_admonitions_defaults(project: Path) -> None:
    settings = load_settings(project)
    assert admonitions(settings, settings.default) == {}
    assert admonitions(settings, settings.language("pt"))["tip"] == "Dica"


def test_admonitions_overrides(project: Path) -> None:
    settings = load_settings(project)
    language = settings.language("pt")
    language.admonition_translations = {"tip": "Sugestão", "todo": "Tarefa"}
    titles = admonitions(settings, language)
    assert titles["tip"] == "Sugestão"
    assert titles["todo"] == "Tarefa"
    assert titles["note"] == "Nota"


def test_admonitions_disabled(project: Path) -> None:
    settings = load_settings(project)
    settings.translate_admonitions = False
    language = settings.language("pt")
    assert admonitions(settings, language) == {}
    language.admonition_translations = {"tip": "Sugestão"}
    assert admonitions(settings, language) == {"tip": "Sugestão"}
