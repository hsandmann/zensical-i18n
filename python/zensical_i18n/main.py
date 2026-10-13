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

import click
from click import ClickException

from zensical_i18n import __version__, builder
from zensical_i18n.settings import I18nError, find_config_file, load_settings

# ----------------------------------------------------------------------------
# Commands
# ----------------------------------------------------------------------------


@click.version_option(version=__version__, message="%(version)s")
@click.group()
def cli() -> None:
    """Zensical i18n - Multi-language sites for Zensical."""


@cli.command(name="build")
@click.option(
    "-f",
    "--config-file",
    type=click.Path(exists=True),
    default=None,
    help="Path to config file.",
)
@click.option(
    "-c",
    "--clean",
    default=False,
    is_flag=True,
    help="Clean cache.",
)
@click.option(
    "-s",
    "--strict",
    default=False,
    is_flag=True,
    help="Enable strict mode - abort the build on warnings.",
)
@click.option(
    "-l",
    "--lang",
    "only",
    metavar="<LOCALE>",
    multiple=True,
    help="Build only the given language - can be repeated.",
)
def execute_build(
    config_file: str | None, clean: bool, strict: bool, only: tuple[str, ...]
) -> None:
    """Build all languages of a project."""
    try:
        settings = load_settings(find_config_file(config_file))
        builder.build(settings, clean=clean, strict=strict, only=list(only))
    except I18nError as e:
        raise ClickException(str(e)) from e


@cli.command(name="serve")
@click.option(
    "-f",
    "--config-file",
    type=click.Path(exists=True),
    default=None,
    help="Path to config file.",
)
@click.option(
    "-l",
    "--lang",
    metavar="<LOCALE>",
    default=None,
    help="Language to serve (default: default language).",
)
@click.option(
    "-a",
    "--dev-addr",
    metavar="<IP:PORT>",
    help="IP address and port (default: localhost:8000).",
)
@click.option(
    "-o",
    "--open",
    "open_browser",
    default=False,
    is_flag=True,
    help="Open preview in default browser.",
)
def execute_serve(
    config_file: str | None,
    lang: str | None,
    dev_addr: str | None,
    open_browser: bool,
) -> None:
    """Build and serve a language of a project."""
    try:
        settings = load_settings(find_config_file(config_file))
        builder.serve(
            settings, lang, dev_addr=dev_addr, open_browser=open_browser
        )
    except I18nError as e:
        raise ClickException(str(e)) from e


# ----------------------------------------------------------------------------
# Program
# ----------------------------------------------------------------------------

if __name__ == "__main__":  # pragma: no cover
    cli()
