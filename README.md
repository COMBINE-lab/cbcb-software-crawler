# CBCB Software Crawler

Prototype crawler and catalog generator for UMD CBCB-affiliated software.

It reads a central `repos.yml`, fetches a `software.yml` metadata file from each
GitHub or GitLab repository, enriches valid entries with repository activity and
version data, and writes a static catalog bundle that can be hosted or adapted
for CBCB's Drupal site. It also includes a local FastAPI admin UI for running
the same crawl from a browser.

## Install

```sh
uv sync --dev
```

Optional environment variables:

```sh
export GITHUB_TOKEN=...
export GITLAB_TOKEN=...
```

Public repositories work without tokens, but tokens improve rate limits and can
allow access to private repositories where the token has permission.

## Input Files

Central repository list:

```yaml
repositories:
  - url: https://github.com/example/tool
  - url: https://gitlab.com/example/tool
```

Each listed repository should contain a root-level `software.yml`:

```yaml
author-lab: Example Lab
name: Example Tool
description: A concise description of the software.
webpage: https://example.org/tool
```

Required fields are `author-lab`, `name`, and `description`. `webpage` is
optional.

## CLI

```sh
uv run cbcb-software-crawler crawl --repos examples/repos.yml --out dist --active-years 2
```

The `--repos` value may be a local path or any URL returning YAML, such as a raw
GitHub URL. You can pass multiple `repos.yml` files in one run:

```sh
uv run cbcb-software-crawler crawl --repos examples/repos.yml https://raw.githubusercontent.com/org/repo/main/repos.yml
```

All repository lists are loaded, checked for duplicate repository URLs after
normalizing GitHub/GitLab owner and project names, and then crawled as one
merged set. Duplicate entries fail the run before any repository scan starts.

Generated files:

- `dist/index.html`: standalone catalog page
- `dist/drupal-fragment.html`: embeddable page fragment
- `dist/software.json`: all valid software entries
- `dist/report.json`: skipped repositories and crawl details
- `dist/report.html`: readable crawl report
- `dist/assets/`: static CSS and JavaScript

## Local Admin UI

```sh
uv run uvicorn cbcb_software_crawler.web:app --reload
```

Open <http://127.0.0.1:8000>, enter one local or remote `repos.yml` per line,
and run the crawl. Results are previewed live and written to `dist/` by default.

## Tests

```sh
uv run pytest
```
