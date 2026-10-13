# Security policy

## Reporting a vulnerability

If you believe you have found a security vulnerability in zensical-i18n, please report it responsibly.

**Please do not report security vulnerabilities through public GitHub issues, pull requests, or discussions.**

Instead, please use [private vulnerability reporting] on GitHub, with the following information:

1. A description of the vulnerability and its potential impact.
2. The steps required to reproduce the issue.
3. Any relevant files, screenshots, or proof-of-concept code.
4. Your name and contact information, if you would like to be credited.

  [private vulnerability reporting]: https://github.com/hsandmann/zensical-i18n/security/advisories/new

## Our commitment

When you submit a report, you can expect the following:

- **Acknowledgement** of your report as soon as possible.
- **Updates** on our progress as we investigate and address the issue.
- **Confidentiality** – we will not share your personal information without your permission, and we ask that you keep the vulnerability confidential until it has been addressed.
- **Credit** – we are happy to acknowledge your contribution once the vulnerability has been resolved, if you would like.

## Supported versions

Security fixes are released for the latest version of zensical-i18n only.

## Scope

This policy applies to vulnerabilities in the zensical-i18n codebase. Vulnerabilities in Zensical itself or other dependencies should be reported to the maintainers of those projects directly.

zensical-i18n builds sites from a project's configuration and sources, which are trusted, as with Zensical and MkDocs – Zensical can, e.g., run Python code from the project with some plugins. Issues that require control over the configuration file are thus only in scope if zensical-i18n makes them more severe than plain Zensical does.
