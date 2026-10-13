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

import pytest

from zensical_i18n.settings import I18nError, load_settings

if TYPE_CHECKING:
    from pathlib import Path

# ----------------------------------------------------------------------------
# Helpers
# ----------------------------------------------------------------------------

# Header of a language entry in zensical.toml.
LANGUAGE = "[[project.plugins.i18n.languages]]\n"


def _write(path: Path, content: str) -> Path:
    """Write a config file and return its path."""
    path.joinpath("docs").mkdir(exist_ok=True)
    path.joinpath("zensical.toml").write_text(content)
    return path / "zensical.toml"


# ----------------------------------------------------------------------------
# Tests
# ----------------------------------------------------------------------------


def test_load_toml(project: Path) -> None:
    settings = load_settings(project)
    assert [lang.locale for lang in settings.languages] == ["en", "pt"]
    assert settings.default.locale == "en"
    assert settings.default.prefix == ""
    assert settings.language("pt").prefix == "pt"
    assert settings.language("pt").overrides == {"site_name": "Documentação"}
    assert settings.fallback_to_default
    assert settings.reconfigure_theme
    assert settings.translate_admonitions


def test_load_mkdocs_yaml(tmp_path: Path) -> None:
    tmp_path.joinpath("docs").mkdir()
    config = tmp_path / "mkdocs.yml"
    config.write_text(
        "site_name: Docs\n"
        "plugins:\n"
        "  - search\n"
        "  - i18n:\n"
        "      reconfigure_material: false\n"
        "      languages:\n"
        "        - locale: en\n"
        "          name: English\n"
        "        - locale: de\n"
        "          name: Deutsch\n"
        "          default: true\n"
    )
    settings = load_settings(config)
    assert settings.default.locale == "de"
    assert not settings.reconfigure_theme


def test_first_language_is_default(tmp_path: Path) -> None:
    config = _write(
        tmp_path,
        '[project]\nsite_name = "x"\n'
        f'{LANGUAGE}locale = "fr"\n{LANGUAGE}locale = "en"\n',
    )
    assert load_settings(config).default.locale == "fr"


@pytest.mark.parametrize(
    "languages",
    [
        f'{LANGUAGE}locale = "en"\n' * 2,
        f'{LANGUAGE}locale = "../en"\n',
        f'{LANGUAGE}name = "English"\n',
        f'{LANGUAGE}locale = "en"\nbuild = false\n',
        f'{LANGUAGE}locale = "en"\ndefault = true\n' * 2,
    ],
)
def test_invalid_languages(tmp_path: Path, languages: str) -> None:
    config = _write(tmp_path, f'[project]\nsite_name = "x"\n{languages}')
    with pytest.raises(I18nError):
        load_settings(config)


def test_missing_plugin(tmp_path: Path) -> None:
    config = _write(tmp_path, '[project]\nsite_name = "x"\n')
    with pytest.raises(I18nError, match="No i18n settings"):
        load_settings(config)


def test_unsupported_docs_structure(tmp_path: Path) -> None:
    config = _write(
        tmp_path,
        '[project]\nsite_name = "x"\n'
        '[project.plugins.i18n]\ndocs_structure = "suffix"\n'
        f'{LANGUAGE}locale = "en"\n',
    )
    with pytest.raises(I18nError, match="suffix"):
        load_settings(config)


def test_admonition_settings(tmp_path: Path) -> None:
    config = _write(
        tmp_path,
        '[project]\nsite_name = "x"\n'
        "[project.plugins.i18n]\ntranslate_admonitions = false\n"
        f'{LANGUAGE}locale = "pt"\n'
        "[project.plugins.i18n.languages.admonition_translations]\n"
        'note = "Observação"\n',
    )
    settings = load_settings(config)
    assert not settings.translate_admonitions
    assert settings.default.admonition_translations == {"note": "Observação"}


# ----------------------------------------------------------------------------


def _project(tmp_path: Path, project: str, languages: str = "") -> Path:
    """Write a project with the given project settings and languages."""
    return _write(
        tmp_path,
        f'[project]\nsite_name = "x"\n{project}'
        + (languages or f'{LANGUAGE}locale = "en"\n'),
    )


@pytest.mark.parametrize(
    "site_dir",
    ["", ".", "./", "..", "../outside", "/outside", "docs", "docs/site"],
)
def test_invalid_site_dir(tmp_path: Path, site_dir: str) -> None:
    config = _project(tmp_path, f'site_dir = "{site_dir}"\n')
    with pytest.raises(I18nError, match="site_dir"):
        load_settings(config)


def test_site_dir_containing_docs(tmp_path: Path) -> None:
    tmp_path.joinpath("out/docs").mkdir(parents=True)
    config = _project(tmp_path, 'site_dir = "out"\ndocs_dir = "out/docs"\n')
    with pytest.raises(I18nError, match="overlap"):
        load_settings(config)


def test_site_dir_symlink_outside(tmp_path: Path) -> None:
    outside = tmp_path / "outside"
    outside.mkdir()
    project = tmp_path / "project"
    project.mkdir()
    project.joinpath("site").symlink_to(outside)
    config = _project(project, "")
    with pytest.raises(I18nError, match="site_dir"):
        load_settings(config)


def test_docs_dir_outside(tmp_path: Path) -> None:
    config = _project(tmp_path, 'docs_dir = "../outside"\n')
    with pytest.raises(I18nError, match="docs_dir"):
        load_settings(config)


@pytest.mark.parametrize(
    "locale",
    ['pt\\" onmouseover=\\"x', "D:", "__proto__", "e", "pt/x", "pt\\nx", ""],
)
def test_invalid_locale(tmp_path: Path, locale: str) -> None:
    config = _project(tmp_path, "", f'{LANGUAGE}locale = "{locale}"\n')
    with pytest.raises(I18nError, match="locale"):
        load_settings(config)


@pytest.mark.parametrize("locale", ["en", "pt_BR", "pt-BR", "zh-Hant-TW"])
def test_valid_locale(tmp_path: Path, locale: str) -> None:
    config = _project(tmp_path, "", f'{LANGUAGE}locale = "{locale}"\n')
    assert load_settings(config).default.locale == locale


def test_yaml_boolean_locale(tmp_path: Path) -> None:
    tmp_path.joinpath("docs").mkdir()
    config = tmp_path / "mkdocs.yml"
    config.write_text(
        "site_name: x\nplugins:\n  - i18n:\n      languages:\n"
        "        - locale: no\n"
    )
    with pytest.raises(I18nError, match="quote"):
        load_settings(config)


@pytest.mark.parametrize(
    "link", ["javascript:alert(1)", " JavaScript:alert(1)", "data:text/html,x"]
)
def test_invalid_link(tmp_path: Path, link: str) -> None:
    config = _project(
        tmp_path, "", f'{LANGUAGE}locale = "en"\nlink = "{link}"\n'
    )
    with pytest.raises(I18nError, match="link"):
        load_settings(config)


@pytest.mark.parametrize("link", ["https://example.com/", "/en/", "../en/"])
def test_valid_link(tmp_path: Path, link: str) -> None:
    config = _project(
        tmp_path, "", f'{LANGUAGE}locale = "en"\nlink = "{link}"\n'
    )
    assert load_settings(config).default.link == link


@pytest.mark.parametrize(
    "setting",
    ['build = "false"', "default = 1", "name = 1", "untranslated_notice = 1"],
)
def test_invalid_types(tmp_path: Path, setting: str) -> None:
    config = _project(tmp_path, "", f'{LANGUAGE}locale = "en"\n{setting}\n')
    with pytest.raises(I18nError):
        load_settings(config)


def test_work_path_symlink(tmp_path: Path) -> None:
    settings = load_settings(_project(tmp_path, ""))
    outside = tmp_path / "outside"
    outside.mkdir()
    settings.work_dir.mkdir()
    settings.work_dir.joinpath("docs").symlink_to(outside)
    with pytest.raises(I18nError, match="symbolic link"):
        settings.work_path("docs", "en")
