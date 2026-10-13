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
import re
import tomllib
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

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
UNSUPPORTED_KEYS = ("fixed_link",)

# Directory for intermediate files, relative to the project root.
WORK_DIR = ".zensical-i18n"

# Locales are BCP 47-like language tags, e.g., `en`, `pt-BR` or `zh_TW`. They
# are used as folder names and in markup, so nothing else is allowed.
LOCALE = re.compile(r"^[A-Za-z]{2,8}(?:[_-][A-Za-z0-9]{1,8})*$")

# Schemes allowed in links to languages - relative links have none.
LINK_SCHEMES = ("", "http", "https")

# Structures of sources: `suffix` (`page.pt.md`, the default, as in
# mkdocs-static-i18n) or `folder` (`pt/page.md`).
DOCS_STRUCTURES = ("suffix", "folder")

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
    admonition_translations: dict[str, str] = field(default_factory=dict)
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
    docs_structure: str = "suffix"
    fallback_to_default: bool = True
    reconfigure_theme: bool = True
    translate_admonitions: bool = True
    warnings: list[str] = field(default_factory=list)

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

    def work_path(self, *parts: str) -> Path:
        """Return a path in the work folder, ensuring it doesn't escape it.

        The work folder and its contents are generated, so symbolic links in
        it can only stem from tampering, and could redirect writes and
        deletions to arbitrary locations - we refuse to follow them.
        """
        path = self.work_dir
        for part in ("", *parts):
            path = path / part if part else path
            if path.is_symlink():
                raise I18nError(f"Refusing to follow symbolic link: {path}")
        if not path.resolve().is_relative_to(self.work_dir.resolve()):
            raise I18nError(f"Path escapes the work folder: {path}")
        return path

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
    structure = options.get("docs_structure")
    if structure is not None and structure not in DOCS_STRUCTURES:
        raise I18nError(
            f"Setting 'docs_structure' must be one of {DOCS_STRUCTURES}."
        )

    # Parse languages and ensure locales are unique
    entries = options.get("languages")
    if not isinstance(entries, list) or not entries:
        raise I18nError("Setting 'languages' must be a non-empty list.")
    warnings: list[str] = []
    languages = [_parse_language(entry, warnings) for entry in entries]
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
    if "reconfigure_theme" not in options and "reconfigure_material" in options:
        options = {
            **options,
            "reconfigure_theme": options["reconfigure_material"],
        }
    settings = Settings(
        config_file=config_file,
        project=project,
        languages=languages,
        docs_structure=structure or "suffix",
        fallback_to_default=_bool(options, "fallback_to_default", True),
        reconfigure_theme=_bool(options, "reconfigure_theme", True),
        translate_admonitions=_bool(options, "translate_admonitions", True),
        warnings=warnings,
    )

    # Validate folders, as the site folder is cleaned when building
    _validate_dirs(settings)

    # Versions before 0.3 defaulted to the folder structure, so we keep using
    # it for projects that use it without setting it, and warn about it
    if structure is None:
        folder = settings.docs_dir / settings.default.locale
        if folder.is_dir():
            settings.docs_structure = "folder"
            settings.warnings.append(
                f"{folder} looks like the folder structure, which is used, "
                "but the default is 'suffix' since 0.3. Set docs_structure = "
                '"folder" in the i18n settings to silence this warning.'
            )

    # Locale folders with the suffix structure would be published as shared
    # files, clashing with the folders of the languages in the site
    if settings.docs_structure == "suffix":
        for lang in languages:
            folder = settings.docs_dir / lang.locale
            if folder.is_dir():
                raise I18nError(
                    f"Found locale folder {folder}, but docs_structure is "
                    "'suffix'. Set docs_structure = \"folder\" to use it."
                )
    return settings


def _validate_dirs(settings: Settings) -> None:
    """Validate the docs and site folders.

    Zensical validates both folders, but only sees the ones we hand it, so we
    apply the same rules to the folders of the project: both must be inside
    the project root, and must be different. As the site folder is cleaned
    before the site is written to it, we additionally ensure it can't contain
    the project root, the docs folder or the work folder, or be contained in
    them. Paths are resolved, so symbolic links can't escape the root.
    """
    for key, default in (("docs_dir", "docs"), ("site_dir", "site")):
        value = settings.project.get(key, default)
        if not isinstance(value, str) or not value.strip():
            raise I18nError(f"Setting '{key}' must be a non-empty string.")

    # Resolve all folders
    root = settings.root.resolve()
    docs_dir = settings.docs_dir.resolve()
    site_dir = settings.site_dir.resolve()
    work_dir = settings.work_dir.resolve()

    # Ensure folders are within the project root
    if not docs_dir.is_relative_to(root):
        raise I18nError(f"docs_dir must be within project root: {docs_dir}")
    if not site_dir.is_relative_to(root) or site_dir == root:
        raise I18nError(
            f"site_dir must be a folder within project root: {site_dir}"
        )
    if site_dir.relative_to(root).parts[0].startswith("."):
        raise I18nError(f"site_dir must not be a hidden folder: {site_dir}")

    # Ensure the site folder doesn't overlap with the docs or work folder
    for name, path in (("docs_dir", docs_dir), (WORK_DIR, work_dir)):
        if site_dir.is_relative_to(path) or path.is_relative_to(site_dir):
            raise I18nError(f"site_dir must not overlap with {name}.")


def _parse_language(entry: Any, warnings: list[str]) -> Language:
    """Parse and validate the settings of a language."""
    if not isinstance(entry, dict) or "locale" not in entry:
        raise I18nError(f"Each language needs a 'locale', got: {entry!r}")

    # Locales are used as folder names and in markup, so they must be tags
    locale = entry["locale"]
    if not isinstance(locale, str) or not LOCALE.fullmatch(locale):
        raise I18nError(
            f"Invalid locale: {locale!r}. Use a language tag like 'en' or "
            "'pt-BR', and quote it in YAML, as, e.g., `no` is a boolean."
        )
    for key in (
        "nav_translations",
        "admonition_translations",
        "theme",
        "extra",
    ):
        if not isinstance(entry.get(key, {}), dict):
            raise I18nError(f"{locale}: '{key}' must be a mapping.")

    # Warn about settings we recognize, but don't implement
    warnings.extend(
        f"{locale}: '{key}' is not supported."
        for key in UNSUPPORTED_KEYS
        if key in entry
    )

    # Links to languages must be relative, or use http(s), as they end up in
    # the href of links, where, e.g., `javascript:` URLs would be executed
    link = _str(entry, "link", locale)
    if link is not None:
        scheme = re.match(r"^([A-Za-z][A-Za-z0-9+.-]*):", link.strip())
        if (scheme and scheme[1].lower() not in LINK_SCHEMES) or (
            not link.isprintable()
        ):
            raise I18nError(f"{locale}: 'link' must be an http(s) URL or path.")

    return Language(
        locale=locale,
        name=_str(entry, "name", locale) or locale,
        default=_bool(entry, "default", False, locale),
        build=_bool(entry, "build", True, locale),
        link=link,
        notice=_str(entry, "untranslated_notice", locale),
        nav_translations=dict(entry.get("nav_translations", {})),
        admonition_translations=dict(entry.get("admonition_translations", {})),
        theme=dict(entry.get("theme", {})),
        extra=dict(entry.get("extra", {})),
        overrides={k: entry[k] for k in OVERRIDABLE_KEYS if k in entry},
    )


def _bool(
    options: dict[str, Any], key: str, default: bool, locale: str = ""
) -> bool:
    """Return a boolean setting, ensuring it's a boolean."""
    value = options.get(key, default)
    if not isinstance(value, bool):
        prefix = f"{locale}: " if locale else ""
        raise I18nError(f"{prefix}'{key}' must be true or false.")
    return value


def _str(entry: dict[str, Any], key: str, locale: str) -> str | None:
    """Return an optional string setting, ensuring it's a string."""
    value = entry.get(key)
    if value is not None and not isinstance(value, str):
        raise I18nError(f"{locale}: '{key}' must be a string.")
    return value
