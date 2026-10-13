# AGENTS.md

Guidance for coding agents working on zensical-i18n. For using the package,
see `README.md` and `llms.txt`.

## Commands

``` sh
uv sync --all-groups                           # install
uv run ruff check . && uv run ruff format .    # lint and format
uv run ty check .                              # type check
uv run pytest                                  # tests (unit and integration)
cd examples/basic && uv run zensical-i18n build   # try the example site
```

All four checks run in CI on Python 3.11 to 3.14 and must pass.

## Layout

- `python/zensical_i18n/` – the package
  - `main.py` – click CLI (`build`, `serve`)
  - `settings.py` – reads `[project.plugins.i18n]` or the `i18n` plugin of
    `mkdocs.yml` (mkdocs-static-i18n schema)
  - `staging.py` – mirrors `docs/<locale>/` into `.zensical-i18n/docs/<locale>`,
    marks fallback pages with `i18n_fallback` front matter, writes the page
    manifest `zensical-i18n.json`
  - `builder.py` – per-language overrides, builds (one subprocess per
    language), per-language cache swapping, assembling `site/`, `serve`
  - `runner.py` – runs inside the subprocess: wraps
    `zensical.config._apply_defaults` to merge overrides, injects our theme
    templates and the admonition Markdown extension, and rehashes
    templates and Markdown configs
  - `discovery.py` – after assembling: hreflang sitemaps, canonical URLs of
    fallback pages, llms.txt links between languages
  - `extensions/admonition.py` – Python-Markdown extension translating
    default admonition titles
  - `languages.py` – built-in translations (notice, admonition titles)
  - `templates/partials/` – language selector, untranslated notice
- `python/tests/` – `unit/`, `integration/` (real builds), `fixtures/project/`
- `examples/basic/` – example site

## Invariants

- Zensical has no plugin API. We depend on private internals
  (`_apply_defaults`, `_list_templates`, `_hash`, `_yaml_load`), so the
  dependency is pinned to `zensical>=0.0.70,<0.1`. Run the full test suite
  before widening it.
- Anything injected after `_apply_defaults` must update the hash Zensical
  uses for change detection (`template_hash`, `mdx_configs_hash`), or builds
  are skipped by the cache.
- Never rewrite staged files or templates that didn't change: Zensical parses
  the config more than once per build, and changed mtimes make it skip
  rendering. Use `staging.sync`.
- Post-processing of the assembled site must be idempotent, as `build --lang`
  reprocesses languages that weren't rebuilt.
- Never touch files outside of `.zensical-i18n/`, `site_dir` and the
  project's `.cache` (which is swapped and always restored). `site_dir` and
  `docs_dir` are validated in `settings.py`, paths in the work folder go
  through `Settings.work_path`, which refuses symbolic links, and
  `staging.sync` never writes through symbolic links.
- Zensical is run with `python -P`, so modules in the project root can't
  shadow installed ones.
- URLs from Zensical are percent-encoded, paths of sources and manifest keys
  aren't: decode URLs before comparing (`discovery.py`, `script.html`), and
  use `staging.encode_url` to match `page.url` in templates.
- Escape every configured string rendered into HTML (`| e`), and validate
  values used in markup or paths in `settings.py` (locales, links).

## Conventions

Follow the conventions of the official zensical/zensical repository:

- MIT license header with SPDX identifier in every Python file, Jinja
  comment header in templates
- `# ----` section dividers (Constants, Classes, Functions, Program)
- Google style docstrings, 80 columns, ruff with `select = ["ALL"]`
- UI built on the theme's components and CSS variables (`md-select`,
  `--md-*`), icons from lucide (modern) or material (classic)
- Commit messages: `<type>: <summary>` with type `feature`, `fix`,
  `performance`, `refactor`, `docs`, `test`, `chore`, `build` or `ci`

## Releasing

Releases happen only through pull requests – never tag or publish manually:

1. Branch `release/v<version>` with exactly one commit
   `chore: release v<version>`, bumping `version` in `pyproject.toml` and
   `uv.lock` (`uv lock`).
2. Open a pull request against `master`. Merging it tags the release, creates
   the GitHub release and publishes to PyPI via trusted publishing.
