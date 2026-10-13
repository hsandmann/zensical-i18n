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
import shutil
import subprocess
from typing import TYPE_CHECKING

import pytest
from bs4 import BeautifulSoup

from zensical_i18n import builder
from zensical_i18n.settings import load_settings

if TYPE_CHECKING:
    from pathlib import Path

# ----------------------------------------------------------------------------
# Constants
# ----------------------------------------------------------------------------

# Origin the site is served from in tests.
ORIGIN = "https://example.com"

# Minimal browser environment for the language selector script, which reads
# the script, manifest and links from the arguments, and prints the links.
HARNESS = """
const [script, manifest, url, data] = process.argv.slice(1).map(JSON.parse)
globalThis.location = new URL(url)
globalThis.window = globalThis
const links = data.links.map(dataset => ({
  dataset, href: "", missing: false,
  toggleAttribute(name, value) { this.missing = value },
}))
const root = {
  dataset: data.root,
  querySelectorAll: () => links,
  addEventListener() {},
  contains: () => false,
}
globalThis.document = {
  readyState: "complete",
  currentScript: { parentElement: root },
  addEventListener() {},
}
globalThis.fetch = async () => ({ ok: true, json: async () => manifest })
new Function(script)()
setTimeout(() => {
  const result = {}
  for (const link of links)
    result[link.dataset.mdI18nLocale] = link.missing ? null : link.href
  console.log(JSON.stringify(result))
}, 10)
"""

# ----------------------------------------------------------------------------
# Fixtures
# ----------------------------------------------------------------------------


@pytest.fixture
def site(project: Path) -> Path:
    """Build the fixture project with special pages and an external link."""
    docs = project.parent / "docs"
    for locale in ("en", "pt"):
        docs.joinpath(locale, "c#sharp.md").write_text("# C#\n")
    project.write_text(
        project.read_text()
        + '\n[[project.plugins.i18n.languages]]\nlocale = "fr"\n'
        + 'build = false\nlink = "https://fr.example.com/"\n'
    )
    builder.build(load_settings(project))
    return project.parent / "site"


# ----------------------------------------------------------------------------
# Helpers
# ----------------------------------------------------------------------------


def _run(site: Path, path: str, url: str) -> dict[str, str | None]:
    """Run the selector script of a page as if visited at the given URL."""
    soup = BeautifulSoup(site.joinpath(path).read_text(), "html.parser")
    root = soup.select_one("[data-md-i18n]")
    assert root is not None
    script = root.select_one("script")
    assert script is not None
    data = {
        "root": {
            "mdI18nBase": root["data-md-i18n-base"],
            "mdI18nManifest": root["data-md-i18n-manifest"],
        },
        "links": [
            {
                "mdI18nLocale": link["data-md-i18n-locale"],
                "mdI18nRoot": link["data-md-i18n-root"],
            }
            for link in root.select("a[data-md-i18n-locale]")
        ],
    }
    manifest = json.loads(site.joinpath("zensical-i18n.json").read_text())
    args = [script.get_text(), manifest, f"{ORIGIN}{url}", data]
    node = shutil.which("node")
    assert node is not None
    result = subprocess.run(  # noqa: S603
        [node, "-e", HARNESS, *map(json.dumps, args)],
        capture_output=True,
        check=True,
        text=True,
    )
    return json.loads(result.stdout)


# ----------------------------------------------------------------------------
# Tests
# ----------------------------------------------------------------------------

pytestmark = pytest.mark.skipif(
    shutil.which("node") is None, reason="node is not installed"
)


def test_links_to_same_page(site: Path) -> None:
    links = _run(site, "pt/guide/install/index.html", "/pt/guide/install/#a")
    assert links["en"] == f"{ORIGIN}/guide/install/#a"
    assert links["pt"] == f"{ORIGIN}/pt/guide/install/#a"


def test_links_to_home_if_missing(site: Path) -> None:
    links = _run(site, "pt/extra/index.html", "/pt/extra/")
    assert links["en"] is None
    assert links["pt"] == f"{ORIGIN}/pt/extra/"


def test_encoded_paths(site: Path) -> None:
    links = _run(site, "pt/c#sharp/index.html", "/pt/c%23sharp/")
    assert links["en"] == f"{ORIGIN}/c%23sharp/"


def test_index_alias(site: Path) -> None:
    links = _run(site, "pt/index.html", "/pt/index.html")
    assert links["en"] == f"{ORIGIN}/index.html"


def test_external_links_are_untouched(site: Path) -> None:
    links = _run(site, "pt/guide/install/index.html", "/pt/guide/install/")
    assert links["fr"] == ""  # left as rendered, i.e., not rewritten
