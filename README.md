# zensical-i18n

Multi-language sites for [Zensical], configured like [mkdocs-static-i18n].

- **One project, many languages** – keep translations next to the originals
  (`page.pt.md`) or in folders (`pt/page.md`), and build all of them into a
  single site, with the default language at the root and every other
  language below `/<locale>/`.
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

Write the default language as usual, and put translations next to the
originals, with the locale as a suffix:

``` sh
.
├─ docs/
│  ├─ assets/
│  │  └─ logo.svg
│  ├─ index.md
│  ├─ index.pt.md
│  └─ guide.md
└─ zensical.toml
```

Links stay the same in all languages, so `index.pt.md` links to `guide.md`
and `assets/logo.svg`. Then, add the languages to `zensical.toml`:

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
`docs/guide.pt.md` doesn't exist, the English guide is used instead, with a
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

## Docs structure

zensical-i18n supports both structures of mkdocs-static-i18n, set with
`docs_structure`:

### Suffix (default)

Translations are files with the locale as a suffix, next to the files of
the default language, which have no suffix. This works for any file, so
`logo.pt.png` is the Portuguese version of `logo.png`:

``` sh
docs/
├─ assets/
│  ├─ logo.png
│  └─ logo.pt.png
├─ index.md
├─ index.pt.md
└─ guide.md
```

A language uses its own files, then files suffixed with the default
locale, e.g., `guide.en.md`, then files without suffix. Only configured
locales are suffixes, so `app.min.js` is left alone, while `lib.es.js` would
be a Spanish file, if `es` is configured. Having both `guide.md` and
`guide.en.md` for the default language `en` is an error.

Link to files without suffix, e.g., `guide.md` or `assets/logo.png`, which
resolves to the file of each language. Links with suffix, e.g.,
`guide.pt.md`, work as well in Markdown, but Zensical reports them as
invalid, as it validates links before they're resolved, which fails builds
with `--strict`. Suffixed links in raw HTML, e.g., `<img src="logo.pt.png">`,
aren't resolved. Pages with a suffix that looks like a locale, which isn't
configured, e.g., `index.de.md`, are reported, as they're built as pages of
their own.

### Folder

Translations are files in a folder named after the locale. Each locale
folder is treated as the docs root, and files outside of locale folders,
like images, are shared by all languages:

``` sh
docs/
├─ assets/
│  └─ logo.png
├─ en/
│  ├─ index.md
│  └─ guide.md
└─ pt/
   └─ index.md
```

Set `docs_structure = "folder"` to use it. A page in `docs/pt/` links to
`assets/logo.png`, not `../assets/logo.png`.

### Choosing a structure

The suffix structure is the default, as in mkdocs-static-i18n and Hugo. It's
easy to see which pages lack translations, and links work the same in all
languages. The folder structure suits projects where translators work
separately, or where languages have different pages.

> [!NOTE]
> Versions before 0.3 only supported the folder structure. Projects with a
> folder named after the default locale, e.g., `docs/en/`, and without
> `docs_structure` keep using it, with a warning to set it explicitly.

## Commands

| Command                 | Description                                       |
| ----------------------- | ------------------------------------------------- |
| `zensical-i18n build`   | Build all languages into a single site            |
| `zensical-i18n serve`   | Build and serve a language with live reload       |

Options of `zensical-i18n build`:

| Option                  | Description                                       |
| ----------------------- | ------------------------------------------------- |
| `-f`, `--config-file`   | Path to the config file                           |
| `-c`, `--clean`         | Clean the cache                                   |
| `-s`, `--strict`        | Abort the build on warnings                       |
| `-l`, `--lang <locale>` | Build only the given language, which can be repeated. The other languages in `site/` are left untouched |

Options of `zensical-i18n serve`:

| Option                  | Description                                       |
| ----------------------- | ------------------------------------------------- |
| `-f`, `--config-file`   | Path to the config file                           |
| `-l`, `--lang <locale>` | Language to serve, instead of the default         |
| `-a`, `--dev-addr`      | IP address and port, e.g. `localhost:8000`        |
| `-o`, `--open`          | Open the preview in the default browser           |

## Settings

Plugin settings:

| Setting               | Default  | Description                                   |
| --------------------- | -------- | --------------------------------------------- |
| `languages`           | –        | Languages of the project, see below           |
| `docs_structure`      | `suffix` | `suffix` (`page.pt.md`) or `folder` (`pt/page.md`), see [Docs structure](#docs-structure) |
| `fallback_to_default` | `true`   | Use pages of the default language when missing |
| `reconfigure_theme`   | `true`   | Add the language selector and untranslated page notice. `reconfigure_material` is supported as an alias |
| `translate_admonitions` | `true` | Use built-in translations for default admonition titles |

Language settings:

| Setting               | Description                                       |
| --------------------- | ------------------------------------------------- |
| `locale`              | Language tag, used as suffix or folder name, e.g. `en`, `pt-BR` or `zh_TW`. Also sets `theme.language`, falling back to the primary language, e.g. `fr` for `fr_CA`, if the theme has no translations for the locale |
| `name`                | Name shown in the language selector               |
| `default`             | Whether this is the default language, built to the site root. Defaults to the first language |
| `build`               | Whether to build the language, defaults to `true`. Languages that aren't built are still listed in the language selector if they have a `link` |
| `link`                | Link in the language selector, e.g., to an external site. Must be an `http(s)` URL or a path |
| `nav_translations`    | Mapping of `nav` titles to their translations     |
| `admonition_translations` | Mapping of admonition types to their default titles, taking precedence over built-in translations |
| `untranslated_notice` | Notice on pages that fall back to the default language, with `{language}` replaced by its name. Plain text, HTML is escaped |
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
  of the original, so their canonical URL points to it, avoiding duplicate
  content. They have no hreflang alternates, but stay in sitemaps, which the
  theme uses for instant navigation.
- **Links without JavaScript** – the language selector links to the same
  page in other languages in the HTML itself, so crawlers follow them.
- **llms.txt** – with Zensical's `llmstxt` plugin enabled, each language gets
  its own llms.txt, and zensical-i18n adds a "Languages" section linking to
  the llms.txt of all other languages.

Independent of `site_url`:

- **Language of content** – the content of fallback pages is marked with the
  language and direction it's written in, e.g., `lang="en" dir="ltr"` on an
  Arabic site, for screen readers, crawlers and LLMs.
- **Edit links** – "edit this page" links point to the source each page was
  built from, e.g., `page.pt.md`, or `page.md` on fallback pages.
- **Head links** – the theme adds links to the home pages of all languages to
  the head of every page, which would declare every page a translation of a
  home page. As sitemaps declare the actual translations, they're removed.

### Using with coding agents

This repository has an [llms.txt] summarizing how to use and configure
zensical-i18n, which you can give to your coding agent, and an
[AGENTS.md] for agents working on zensical-i18n itself.

  [llms.txt]: https://raw.githubusercontent.com/hsandmann/zensical-i18n/master/llms.txt
  [AGENTS.md]: https://github.com/hsandmann/zensical-i18n/blob/master/AGENTS.md

## How it works

Zensical doesn't have plugin hooks yet, so zensical-i18n runs Zensical once
per language:

1. **Staging** – the sources of each language are mirrored into
   `.zensical-i18n/docs/<locale>/`, layering the language's files over those
   of the default language and the shared files, and removing suffixes.
2. **Building** – Zensical builds each language in a separate process, with
   the language's settings merged in after Zensical has parsed the config file,
   so YAML tags, `INHERIT` and relative paths keep working. Each language has
   its own cache, so incremental builds stay fast.
3. **Assembling** – the outputs are merged into `site_dir`, with the default
   language at the root and all others below their locale.

The language selector reads `zensical-i18n.json`, a manifest of the pages of
all languages written to each language's root, to keep readers on the same
page while navigating.

Add `.zensical-i18n` to your `.gitignore`.

### Safety

The site folder is cleaned before the site is written to it, so `site_dir`
must be a folder within the project, and must not overlap with `docs_dir` or
`.zensical-i18n`. Hidden files in it, like `.git` or `.nojekyll`, are kept.
zensical-i18n refuses to follow symbolic links in its work folder, and runs
Zensical so that Python files in the project root can't shadow installed
modules.

## Limitations

- Search covers the language that is currently shown.
- `serve` previews one language at a time.
- The language selector and notice replace the theme's
  `partials/alternate.html` and wrap `partials/content.html`. A custom
  `alternate.html` in `custom_dir` is ignored while `reconfigure_theme` is
  enabled.
- Edit links are fixed by wrapping the theme's `partials/actions.html`,
  independent of `reconfigure_theme`. A custom `partials/content.html` that
  renders the edit buttons itself, instead of including `actions.html`,
  links to the staged files.

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
[internationalization]: https://zensical.org/roadmap/#internationalization
