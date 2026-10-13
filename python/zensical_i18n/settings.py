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

import os
import tomllib
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import click
from zensical import config as zensical_config

# ----------------------------------------------------------------------------
# Constants
# ----------------------------------------------------------------------------

# Per-language settings that are copied verbatim over the project settings.
OVERRIDABLE_KEYS = (
    "site_name",
    "site_description",
    "site_author",
    "copyright",
    "nav",
)

# Settings of mkdocs-static-i18n that are recognized, but not implemented.
UNSUPPORTED_KEYS = ("admonition_translations", "fixed_link")

# Directory for intermediate files, relative to the project root.
WORK_DIR = ".zensical-i18n"

# ----------------------------------------------------------------------------
# Classes
# ----------------------------------------------------------------------------


class I18nError(Exception):
    """Invalid i18n configuration or failed build step."""


@dataclass
class Language:
    """A language of the project."""

    locale: str
    name: str
    default: bool = False
    build: bool = True
    link: str | None = None
    notice: str | None = None
    nav_translations: dict[str, str] = field(default_factory=dict)
    theme: dict[str, Any] = field(default_factory=dict)
    extra: dict[str, Any] = field(default_factory=dict)
    overrides: dict[str, Any] = field(default_factory=dict)

    @property
    def prefix(self) -> str:
        """Path of the language's output, relative to the site root."""
        return "" if self.default else self.locale


@dataclass
class Settings:
    """The project configuration, together with its i18n settings."""

    config_file: Path
    project: dict[str, Any]
    languages: list[Language]
    fallback_to_default: bool = True
    reconfigure_theme: bool = True

    @property
    def root(self) -> Path:
        """Project root, which is the folder of the config file."""
        return self.config_file.parent

    @property
    def docs_dir(self) -> Path:
        """Folder with the per-language sources."""
        return self.root / self.project.get("docs_dir", "docs")

    @property
    def site_dir(self) -> Path:
        """Folder the assembled site is written to."""
        return self.root / self.project.get("site_dir", "site")

    @property
    def work_dir(self) -> Path:
        """Folder for staged sources and per-language builds."""
        return self.root / WORK_DIR

    @property
    def directory_urls(self) -> bool:
        """Whether pages are rendered to `page/index.html`."""
        return bool(self.project.get("use_directory_urls", True))

    @property
    def default(self) -> Language:
        """The default language, which is built to the site root."""
        return next(lang for lang in self.languages if lang.default)

    @property
    def built(self) -> list[Language]:
        """Languages that are part of the build."""
        return [lang for lang in self.languages if lang.build]

    def language(self, locale: str) -> Language:
        """Return the language for the given locale."""
        for lang in self.languages:
            if lang.locale == locale:
                return lang
        raise I18nError(f"Unknown locale: {locale}")


# ----------------------------------------------------------------------------
# Functions
# ----------------------------------------------------------------------------


def find_config_file(path: str | None) -> Path:
    """Resolve the config file, looking it up the same way Zensical does."""
    if path is not None:
        return Path(path).resolve()
    for name in ("zensical.toml", "mkdocs.yml", "mkdocs.yaml"):
        if os.path.exists(name):
            return Path(name).resolve()
    raise I18nError("No config file found in the current folder.")


def load_settings(config_file: Path) -> Settings:
    """Load the project configuration and extract the i18n settings.

    Settings are read from the `i18n` plugin, which is `[project.plugins.i18n]`
    in `zensical.toml`, and the `i18n` entry of `plugins` in `mkdocs.yml`,
    using the same schema as mkdocs-static-i18n. Zensical ignores plugins it
    doesn't know, so the configuration can be shared with plain builds.
    """
    if config_file.suffix.lower() == ".toml":
        with open(config_file, "rb") as f:
            data = tomllib.load(f)
        project = data.get("project", data)
    else:
        with open(config_file, encoding="utf-8") as f:
            project = zensical_config._yaml_load(f)

    # Extract plugin settings - plugins can be defined as a list or mapping
    options = None
    plugins = project.get("plugins")
    if isinstance(plugins, dict):
        options = plugins.get("i18n")
    elif isinstance(plugins, list):
        for entry in plugins:
            if isinstance(entry, dict) and "i18n" in entry:
                options = entry["i18n"]

    # Ensure plugin is configured
    if not isinstance(options, dict):
        raise I18nError(
            f"No i18n settings found in {config_file.name}. Configure the "
            "`i18n` plugin, e.g., in [project.plugins.i18n]."
        )
    return _parse_settings(config_file, project, options)


# ----------------------------------------------------------------------------


def _parse_settings(
    config_file: Path, project: dict[str, Any], options: dict[str, Any]
) -> Settings:
    """Parse and validate plugin settings."""
    structure = options.get("docs_structure", "folder")
    if structure != "folder":
        raise I18nError(f"Unsupported docs_structure '{structure}'.")

    # Parse languages and ensure locales are unique
    entries = options.get("languages")
    if not isinstance(entries, list) or not entries:
        raise I18nError("Setting 'languages' must be a non-empty list.")
    languages = [_parse_language(entry) for entry in entries]
    locales = [lang.locale for lang in languages]
    if len(set(locales)) != len(locales):
        raise I18nError(f"Duplicate locales: {locales}")

    # Ensure there's exactly one default language, defaulting to the first
    defaults = [lang for lang in languages if lang.default]
    if len(defaults) > 1:
        raise I18nError("Only one language can be marked as default.")
    if not defaults:
        languages[0].default = True
    if not next(lang for lang in languages if lang.default).build:
        raise I18nError("The default language must be built.")

    # Support the setting name used by mkdocs-static-i18n as well
    reconfigure = options.get(
        "reconfigure_theme", options.get("reconfigure_material", True)
    )
    return Settings(
        config_file=config_file,
        project=project,
        languages=languages,
        fallback_to_default=bool(options.get("fallback_to_default", True)),
        reconfigure_theme=bool(reconfigure),
    )


def _parse_language(entry: Any) -> Language:
    """Parse and validate the settings of a language."""
    if not isinstance(entry, dict) or not entry.get("locale"):
        raise I18nError(f"Each language needs a 'locale', got: {entry!r}")

    # Locales are used as folder names, so they must be plain names
    locale = str(entry["locale"])
    if "/" in locale or "\\" in locale or locale.startswith("."):
        raise I18nError(f"Invalid locale: {locale!r}")
    for key in ("nav_translations", "theme", "extra"):
        if not isinstance(entry.get(key, {}), dict):
            raise I18nError(f"{locale}: '{key}' must be a mapping.")

    # Warn about settings we recognize, but don't implement
    for key in UNSUPPORTED_KEYS:
        if key in entry:
            click.echo(f"Warning: {locale}: '{key}' is not supported.")

    return Language(
        locale=locale,
        name=str(entry.get("name", locale)),
        default=bool(entry.get("default", False)),
        build=bool(entry.get("build", True)),
        link=entry.get("link"),
        notice=entry.get("untranslated_notice"),
        nav_translations=dict(entry.get("nav_translations", {})),
        theme=dict(entry.get("theme", {})),
        extra=dict(entry.get("extra", {})),
        overrides={k: entry[k] for k in OVERRIDABLE_KEYS if k in entry},
    )
