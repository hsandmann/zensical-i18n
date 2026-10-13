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
import posixpath
import shutil
import signal
import subprocess
import sys
import time
from contextlib import contextmanager
from pathlib import Path
from typing import TYPE_CHECKING, Any

import click

from zensical_i18n import discovery, languages, nav, staging
from zensical_i18n.settings import I18nError, Language, Settings, load_settings

if TYPE_CHECKING:
    from collections.abc import Generator

# ----------------------------------------------------------------------------
# Constants
# ----------------------------------------------------------------------------

# Cache folder of Zensical, relative to the project root.
CACHE_DIR = ".cache"

# Names of the stashed project cache and the swapped in language marker,
# which can't clash with locales, as those can't start with a dot.
CACHE_PROJECT = ".project"
CACHE_ACTIVE = ".active"

# ----------------------------------------------------------------------------
# Functions
# ----------------------------------------------------------------------------


def overrides(settings: Settings, language: Language) -> dict[str, Any]:
    """Return the settings that turn the project into a language's site."""
    project = settings.project
    work_dir = settings.work_dir.relative_to(settings.root)
    result: dict[str, Any] = {
        "docs_dir": str(work_dir / "docs" / language.locale),
        "site_dir": str(work_dir / "site" / language.locale),
        "theme": dict(language.theme),
    }

    # Every language is published below the site URL of the project
    if project.get("site_url"):
        site_url = project["site_url"].rstrip("/") + "/"
        if language.prefix:
            site_url += f"{language.prefix}/"
        result["site_url"] = site_url

    # Translate titles of the navigation, if defined
    if "nav" in project:
        result["nav"] = nav.translate(project["nav"], language.nav_translations)

    # Point edit links to the actual sources of pages, by encoded page URL,
    # with the paths in the staged and actual docs folder, raw and encoded
    extra = dict(language.extra)
    extra["i18n_edits"] = {
        staging.encode_url(url): [
            page.src,
            page.source,
            staging.encode_url(page.src),
            staging.encode_url(page.source),
        ]
        for url, page in staging.page_sources(settings, language).items()
        if page.source and page.source != page.src
    }

    # Configure the language selector and the untranslated page notice, and
    # list languages that aren't built, but link to an external site
    if settings.reconfigure_theme:
        links = [
            {
                "name": other.name,
                "lang": languages.hreflang(other.locale),
                "locale": other.locale,
                "link": _link(language, other),
            }
            for other in settings.languages
            if other.build or other.link
        ]
        extra["alternate"] = links
        extra["i18n"] = {
            "locale": language.locale,
            "lang": languages.hreflang(language.locale),
            "dir": languages.direction(language.locale),
            "prefix": f"{language.prefix}/" if language.prefix else "",
            "manifest": staging.MANIFEST,
            "languages": links,
            "pages": {
                lang.locale: sorted(
                    staging.encode_url(url)
                    for url in staging.pages(settings, lang)
                )
                for lang in settings.built
            },
            "notice": languages.notice(
                language.locale, settings.default.name, language.notice
            ),
        }
    if extra:
        result["extra"] = extra

    # Apply language-specific settings last, so they take precedence
    result.update(language.overrides)
    return result


def admonitions(settings: Settings, language: Language) -> dict[str, str]:
    """Return the admonition titles of a language.

    Built-in titles for the language are used, unless disabled, with titles
    configured for the language taking precedence.
    """
    titles = {}
    if settings.translate_admonitions:
        titles = languages.admonitions(language.locale)
    return {**titles, **language.admonition_translations}


def stage(settings: Settings, language: Language) -> None:
    """Synchronize the staged docs folder of a language with its sources."""
    files = staging.collect(settings, language)
    if settings.reconfigure_theme:
        data = staging.manifest(settings)
        files[Path(staging.MANIFEST)] = staging.Source(data=data)
    staging.sync(files, settings.work_path("docs", language.locale))


def build(
    settings: Settings,
    *,
    clean: bool = False,
    strict: bool = False,
    only: list[str] | None = None,
) -> None:
    """Build all or the given languages, and assemble the site."""
    _warn(settings)
    selected = settings.built
    if only:
        unknown = set(only) - {lang.locale for lang in selected}
        if unknown:
            raise I18nError(f"Unknown or disabled locales: {sorted(unknown)}")
        selected = [lang for lang in selected if lang.locale in only]

    # Build languages one after another, each with its own cache
    for language in selected:
        click.echo(f"Building '{language.locale}' ({language.name})")
        stage(settings, language)
        options = {"clean": clean, "strict": strict}
        with cache(settings, language):
            result = subprocess.run(  # noqa: S603
                _command("build", settings, language, options),
                cwd=settings.root,
                check=False,
            )
        if result.returncode != 0:
            raise I18nError(f"Build of '{language.locale}' failed.")

    # Assemble site from the outputs of all languages
    assemble(settings, selected)


def assemble(settings: Settings, selected: list[Language]) -> None:
    """Assemble the site, with the default language at the root.

    Other languages are placed in folders named after their locale. When only
    some languages were built, the outputs of the others are left untouched,
    while folders of languages that aren't built anymore are removed.
    """
    site_dir = settings.site_dir
    locales = {lang.locale for lang in settings.built if not lang.default}

    # Copy default language, keeping the folders of other languages, as well
    # as hidden files like .git or .nojekyll, which Zensical keeps as well
    default = settings.default
    if default in selected:
        output = settings.work_path("site", default.locale)
        all_locales = {lang.locale.casefold() for lang in settings.languages}
        clashes = {
            path.name
            for path in output.iterdir()
            if path.name.casefold() in all_locales
        }
        if clashes:
            raise I18nError(
                f"Output of the default language contains {sorted(clashes)}, "
                "which clash with the folders of other languages."
            )
        _replace(output, site_dir, keep=locales, keep_hidden=True)

    # Copy other languages
    for language in selected:
        if not language.default:
            output = settings.work_path("site", language.locale)
            _replace(output, site_dir / language.locale)

    # Declare translations to search engines and LLMs
    discovery.publish(settings)
    click.echo(f"Site written to {site_dir}")


def serve(
    settings: Settings,
    locale: str | None = None,
    *,
    dev_addr: str | None = None,
    open_browser: bool = False,
    interval: float = 0.5,
) -> None:
    """Serve a language, keeping its staged docs folder in sync.

    Zensical watches the staged docs folder, which we keep in sync with the
    sources. Changes to the config file are picked up by Zensical, as the
    language's settings are recomputed whenever Zensical parses it.
    """
    language = settings.language(locale) if locale else settings.default
    _warn(settings)
    stage(settings, language)
    options = {"dev_addr": dev_addr, "open": open_browser, "strict": False}

    # Shut down gracefully when terminated, stopping Zensical and restoring
    # the project's cache, which a plain SIGTERM would skip
    signal.signal(signal.SIGTERM, lambda *_: sys.exit(0))
    with cache(settings, language):
        child = subprocess.Popen(  # noqa: S603
            _command("serve", settings, language, options),
            cwd=settings.root,
        )
        _watch(settings, language, child, interval)

    # Report if Zensical failed, e.g., as the address is already in use
    if child.returncode not in (0, 130, -signal.SIGINT, -signal.SIGTERM):
        raise I18nError(f"Zensical exited with status {child.returncode}.")


@contextmanager
def cache(settings: Settings, language: Language) -> Generator[None]:
    """Give Zensical a separate cache for the given language.

    Zensical keeps its cache in the project root. As the configuration differs
    for each language, a shared cache would be invalidated on every switch, so
    we swap in the language's cache, and restore the project's cache after.
    The swapped in language is recorded, so an interrupted run is recovered.
    """
    current = settings.root / CACHE_DIR
    caches = settings.work_path("cache")
    caches.mkdir(parents=True, exist_ok=True)
    locales = {lang.locale for lang in settings.languages}
    _restore_cache(current, caches, locales)

    # Stash the project's cache, record the language, and only then swap in
    # the language's cache, so an interruption at any point is recovered
    if current.exists() or current.is_symlink():
        current.rename(caches / CACHE_PROJECT)
    caches.joinpath(CACHE_ACTIVE).write_text(language.locale, encoding="utf-8")
    stored = settings.work_path("cache", language.locale)
    if stored.exists():
        stored.rename(current)
    try:
        yield
    finally:
        _restore_cache(current, caches, locales)


# ----------------------------------------------------------------------------


def _watch(
    settings: Settings,
    language: Language,
    child: subprocess.Popen,
    interval: float,
) -> None:
    """Synchronize sources until Zensical exits, reloading settings."""
    config_mtime = settings.config_file.stat().st_mtime
    try:
        while child.poll() is None:
            time.sleep(interval)
            # Keep serving on errors, e.g., when the config file is saved with
            # a syntax error, which Zensical reports as well
            try:
                mtime = settings.config_file.stat().st_mtime
                if mtime != config_mtime:
                    config_mtime = mtime
                    settings = load_settings(settings.config_file)
                    language = settings.language(language.locale)
                stage(settings, language)
            except Exception as e:  # noqa: BLE001
                click.echo(f"Error: {e}")
    except KeyboardInterrupt:
        pass
    finally:
        if child.poll() is None:
            child.terminate()
            child.wait()


def _restore_cache(current: Path, caches: Path, locales: set[str]) -> None:
    """Store the swapped in language cache, and restore the project's.

    The marker is only trusted if it names a known locale, as its contents
    determine which folder is replaced.
    """
    marker = caches / CACHE_ACTIVE
    if marker.exists():
        locale = marker.read_text(encoding="utf-8")
        stored = caches / locale
        if locale in locales and not stored.is_symlink() and current.exists():
            if stored.exists():
                shutil.rmtree(stored)
            current.rename(stored)
        marker.unlink()

    # If the project has a newer cache, the stashed one is stale
    project = caches / CACHE_PROJECT
    if project.exists() or project.is_symlink():
        if current.exists() or current.is_symlink():
            _remove(project)
        else:
            project.rename(current)


def _warn(settings: Settings) -> None:
    """Print warnings about settings and sources, once per run."""
    for warning in [*settings.warnings, *staging.check(settings)]:
        click.echo(f"Warning: {warning}")


def _link(current: Language, target: Language) -> str:
    """Return the link from a language's site root to another one's."""
    if target.link:
        return target.link
    path = posixpath.relpath(target.prefix or ".", current.prefix or ".")
    return "./" if path == "." else f"{path}/"


def _command(
    command: str, settings: Settings, language: Language, options: dict
) -> list[str]:
    """Return the command to run Zensical for a language.

    Python is run with `-P`, so modules in the project root, which is the
    working directory, can't shadow installed modules and run on import.
    """
    return [
        sys.executable,
        "-P",
        "-m",
        "zensical_i18n.runner",
        command,
        str(settings.config_file),
        language.locale,
        json.dumps(options),
    ]


def _replace(
    src: Path,
    dest: Path,
    keep: set[str] | None = None,
    *,
    keep_hidden: bool = False,
) -> None:
    """Replace the contents of a folder, except for the given entries."""
    if dest.is_symlink():
        raise I18nError(f"Refusing to replace symbolic link: {dest}")
    if dest.exists():
        for path in dest.iterdir():
            if keep and path.name in keep:
                continue
            if keep_hidden and path.name.startswith("."):
                continue
            _remove(path)
    shutil.copytree(src, dest, dirs_exist_ok=True)


def _remove(path: Path) -> None:
    """Remove a file or folder, without following symbolic links."""
    if path.is_dir() and not path.is_symlink():
        shutil.rmtree(path)
    else:
        path.unlink()
