# zensical-i18n

Multi-language sites for [Zensical], configured like [mkdocs-static-i18n].

- **One project, many languages** – keep translations in `docs/<locale>/`
  folders and build all of them into a single site, with the default language
  at the root and every other language below `/<locale>/`.
- **Language selector** – a selector in the header that matches Zensical's
  modern and classic variants, light and dark color schemes, and takes readers
  to the same page in the other language when it exists.
- **Fallback to the default language** – pages that aren't translated yet are
  taken from the default language and marked with a short notice in the
  reader's language.
- **Translated navigation** – titles in `nav` are translated per language,
  and each language can override settings like `site_name` or `copyright`.
- **Translated admonitions** – default titles of admonitions like
  `!!! note` are translated, e.g., to "Nota" in Portuguese, out of the box
  for over 20 languages.
- **Search engines and LLMs** – translations are declared in hreflang
  sitemaps, untranslated pages point to their originals, and the llms.txt
  files of all languages link to each other.

> [!NOTE]
> Zensical doesn't support multi-language sites or third-party plugins yet.
> Built-in [internationalization] is on the Zensical roadmap and will likely
> make this project obsolete. Until then, zensical-i18n wraps the `zensical`
> command. It hooks into Zensical's configuration internals, so each release
> is tested against a specific range of Zensical versions.

## Quick start

Install zensical-i18n with:

``` sh
pip install zensical-i18n
```

Put the sources of each language in a folder named after its locale. Files
outside of locale folders, like images, are shared by all languages:

``` sh
.
├─ docs/
│  ├─ assets/
│  │  └─ logo.svg
│  ├─ en/
│  │  ├─ index.md
│  │  └─ guide.md
│  └─ pt/
│     └─ index.md
└─ zensical.toml
```

Each locale folder is treated as the docs root, so `docs/pt/index.md` links to
`assets/logo.svg` and `guide.md`. Then, add the languages to `zensical.toml`:

``` toml
[project]
site_name = "Documentation"
site_url = "https://example.com/"
nav = [
  { "Get started" = "index.md" },
  { "Guide" = "guide.md" },
]

[project.plugins.i18n]

[[project.plugins.i18n.languages]]
locale = "en"
name = "English"
default = true

[[project.plugins.i18n.languages]]
locale = "pt"
name = "Português"
site_name = "Documentação"

[project.plugins.i18n.languages.nav_translations]
"Get started" = "Comece aqui"
"Guide" = "Guia"
```

Build the site with:

``` sh
zensical-i18n build
```

This builds `site/` with English at the root and Portuguese in `site/pt/`. As
`docs/pt/guide.md` doesn't exist, the English guide is used instead, with a
notice that it hasn't been translated yet.

While writing, preview a language with live reload:

``` sh
zensical-i18n serve --lang pt
```

### Using mkdocs.yml

Projects using `mkdocs.yml` are supported as well, using the same settings as
mkdocs-static-i18n:

``` yaml
plugins:
  - search
  - i18n:
      docs_structure: folder
      languages:
        - locale: en
          name: English
          default: true
        - locale: pt
          name: Português
          site_name: Documentação
          nav_translations:
            Get started: Comece aqui
```

## Commands

| Command                 | Description                                       |
| ----------------------- | ------------------------------------------------- |
| `zensical-i18n build`   | Build all languages into a single site            |
| `zensical-i18n serve`   | Build and serve a language with live reload       |

Both commands accept the options of the corresponding `zensical` commands,
like `--config-file`, `--clean`, `--strict` or `--dev-addr`, as well as:

- `build --lang <locale>` – build only the given language, which can be
  repeated. The other languages in `site/` are left untouched.
- `serve --lang <locale>` – serve the given language instead of the default.

## Settings

Plugin settings:

| Setting               | Default  | Description                                   |
| --------------------- | -------- | --------------------------------------------- |
| `languages`           | –        | Languages of the project, see below           |
| `docs_structure`      | `folder` | Only `folder` is supported                    |
| `fallback_to_default` | `true`   | Use pages of the default language when missing |
| `reconfigure_theme`   | `true`   | Add the language selector and untranslated page notice. `reconfigure_material` is supported as an alias |
| `translate_admonitions` | `true` | Use built-in translations for default admonition titles |

Language settings:

| Setting               | Description                                       |
| --------------------- | ------------------------------------------------- |
| `locale`              | Locale and folder name, e.g. `en` or `pt-BR`. Also sets `theme.language` |
| `name`                | Name shown in the language selector               |
| `default`             | Whether this is the default language, built to the site root. Defaults to the first language |
| `build`               | Whether to build the language, defaults to `true` |
| `link`                | Link in the language selector, e.g., to an external site |
| `nav_translations`    | Mapping of `nav` titles to their translations     |
| `admonition_translations` | Mapping of admonition types to their default titles, taking precedence over built-in translations |
| `untranslated_notice` | Notice on pages that fall back to the default language, with `{language}` replaced by its name |
| `site_name`, `site_description`, `site_author`, `copyright`, `nav` | Override the project setting |
| `theme`, `extra`      | Merged into the project setting                   |

## Admonitions

Admonitions without a title get one derived from their type, e.g., "Note"
for `!!! note`. zensical-i18n translates these default titles for each
language, for all admonition syntaxes (`!!!`, `???` and `///`), while titles
given explicitly are left untouched:

``` markdown
!!! note
    Rendered with the title "Nota" in Portuguese.

!!! note "Leia isto"
    Rendered with the title "Leia isto".
```

Built-in translations cover the types of the theme – `note`, `abstract`,
`info`, `tip`, `success`, `question`, `warning`, `failure`, `danger`, `bug`,
`example` and `quote`. Translate other types, or change the built-in
translations, with `admonition_translations`:

``` toml
[[project.plugins.i18n.languages]]
locale = "pt"
name = "Português"

[project.plugins.i18n.languages.admonition_translations]
note = "Observação"
todo = "Tarefa"
```

An explicit title that equals the default title, like `!!! note "Note"`, is
indistinguishable from a default title, and thus translated as well.

## Search engines and LLMs

When `site_url` is set, zensical-i18n makes the translations of a site
discoverable by search engines, crawlers and LLMs:

- **hreflang sitemaps** – the sitemap of each language lists the
  translations of every page, including an `x-default` pointing to the
  default language, which search engines treat like hreflang links in the
  head of pages.
- **Canonical URLs** – pages falling back to the default language are copies
  of the original, so their canonical URL points to it, and they're left out
  of sitemaps, avoiding duplicate content.
- **Language of content** – the content of fallback pages is marked with the
  language it's written in, e.g., `lang="en"` on a Portuguese site, for
  screen readers, crawlers and LLMs.
- **Links without JavaScript** – the language selector links to the same
  page in other languages in the HTML itself, so crawlers follow them.
- **llms.txt** – with Zensical's `llmstxt` plugin enabled, each language gets
  its own llms.txt, and zensical-i18n adds a "Languages" section linking to
  the llms.txt of all other languages.

The theme adds links to the home pages of all languages to the head of every
page, which would declare every page a translation of a home page. As the
sitemaps declare the actual translations, zensical-i18n removes these links.

## How it works

Zensical doesn't have plugin hooks yet, so zensical-i18n runs Zensical once
per language:

1. **Staging** – the sources of each language are mirrored into
   `.zensical-i18n/docs/<locale>/`, layering the language's files over those
   of the default language and the shared files.
2. **Building** – Zensical builds each language in a separate process, with
   the language's settings merged in after Zensical has parsed the config file,
   so YAML tags, `INHERIT` and relative paths keep working. Each language has
   its own cache, so incremental builds stay fast.
3. **Assembling** – the outputs are merged into `site_dir`, with the default
   language at the root and all others below their locale.

The language selector reads `zensical-i18n.json`, a manifest of the pages of
all languages written to each language's root. Without JavaScript, the
selector links to the home page of each language.

Add `.zensical-i18n` to your `.gitignore`.

## Limitations

- Only the folder structure is supported, not suffixes like `index.pt.md`.
- Search covers the language that is currently shown.
- `serve` previews one language at a time.

## Contributing

Commit messages follow the format `<type>: <summary>`, where type is one of
`feature`, `fix`, `performance`, `refactor`, `docs`, `test`, `chore`, `build`
or `ci`. Run the checks with:

``` sh
uv sync --all-groups
uv run ruff check . && uv run ruff format --check .
uv run ty check .
uv run pytest
```

### Releasing

New versions are released through pull requests:

1. Create a branch named `release/v<version>`, e.g., `release/v0.2.0`.
2. Bump `version` in `pyproject.toml`, run `uv lock`, and commit both with
   the message `chore: release v<version>` – the branch must contain exactly
   this one commit.
3. Open a pull request against `master`. Once it's merged, the tag, the
   GitHub release and the upload to PyPI are created automatically.

## License

**MIT License**

Copyright (c) 2026 Humberto Sandmann and contributors

[Zensical]: https://zensical.org
[mkdocs-static-i18n]: https://github.com/ultrabug/mkdocs-static-i18n
[internationalization]: https://zensical.org/about/roadmap/#internationalization
