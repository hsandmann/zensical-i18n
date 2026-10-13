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
import sys
from pathlib import Path
from typing import Any

from zensical import build, serve
from zensical import config as zensical_config

from zensical_i18n.builder import overrides
from zensical_i18n.settings import load_settings
from zensical_i18n.staging import Source, sync

# ----------------------------------------------------------------------------
# Constants
# ----------------------------------------------------------------------------

# Templates of the language selector and untranslated page notice.
TEMPLATES = Path(__file__).parent / "templates"

# Partial that our content partial wraps, copied from the theme in use.
CONTENT = "partials/content.html"
CONTENT_ORIGINAL = "partials/i18n/original-content.html"

# ----------------------------------------------------------------------------
# Functions
# ----------------------------------------------------------------------------


def merge(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    """Recursively merge mappings, replacing all other values."""
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(base.get(key), dict):
            merge(base[key], value)
        else:
            base[key] = value
    return base


def install(locale: str) -> None:
    """Hook into Zensical's configuration for the given language.

    Zensical doesn't support third-party plugins yet, so we wrap the step that
    applies defaults after parsing. This way, Zensical parses the config file
    itself (keeping YAML tags, INHERIT and relative paths intact), and we merge
    the language's settings before defaults are applied. Settings are computed
    on every parse, so config reloads during `serve` pick up changes as well.
    """
    apply_defaults = zensical_config._apply_defaults

    def patched(config: dict, path: str) -> dict:
        settings = load_settings(Path(path).resolve())
        language = settings.language(locale)
        merge(config, overrides(settings, language))
        config = apply_defaults(config, path)

        # Add templates of the language selector and notice, if enabled
        if settings.reconfigure_theme:
            theme_dir = settings.work_dir / "theme"
            _prepare_theme(theme_dir, config["theme_dirs"])
            config["theme_dirs"] = [str(theme_dir), *config["theme_dirs"]]

            # Rehash templates, so changes to ours trigger a rebuild as well
            templates = zensical_config._list_templates(config)
            config["template_hash"] = zensical_config._hash(templates)
        return config

    zensical_config._apply_defaults = patched  # ty:ignore[invalid-assignment]


def main() -> None:
    """Run Zensical for a language - invoked by the builder."""
    command, config_file, locale, options = sys.argv[1:5]
    install(locale)
    run = build if command == "build" else serve
    run(config_file, json.loads(options))


# ----------------------------------------------------------------------------


def _prepare_theme(theme_dir: Path, theme_dirs: list[str]) -> None:
    """Prepare our templates on top of the theme in use.

    The content partial of the theme in use, which might be customized by the
    author, is copied next to our templates, so ours can wrap it. Zensical may
    parse the configuration more than once, so only changes are written, as
    rewriting templates during a build makes Zensical skip rendering.
    """
    files = {
        path.relative_to(TEMPLATES): Source(path)
        for path in TEMPLATES.rglob("*")
        if path.is_file()
    }
    for path in theme_dirs:
        content = Path(path) / CONTENT
        if content.is_file():
            files[Path(CONTENT_ORIGINAL)] = Source(content)
            break

    # Synchronize templates
    sync(files, theme_dir)


# ----------------------------------------------------------------------------
# Program
# ----------------------------------------------------------------------------

if __name__ == "__main__":
    main()
