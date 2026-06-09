from pathlib import Path
from typing import Any, Dict, Iterable, List, Sequence, Union
from urllib.parse import urlparse

import yaml

from .errors import ValidationError
from .http import fetch_text
from .models import RepositoryRef, SoftwareMetadata


REQUIRED_METADATA_FIELDS = ("author-lab", "name", "description")


def is_url(value: str) -> bool:
    parsed = urlparse(value)
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc)


def load_yaml_source(source: str) -> Dict[str, Any]:
    text = fetch_text(source) if is_url(source) else Path(source).read_text(encoding="utf-8")
    loaded = yaml.safe_load(text)
    if not isinstance(loaded, dict):
        raise ValidationError("YAML source must contain a mapping at the top level")
    return loaded


ReposSources = Union[str, Sequence[str]]


def parse_repos(source: str) -> List[RepositoryRef]:
    data = load_yaml_source(source)
    repositories = data.get("repositories")
    if not isinstance(repositories, list):
        raise ValidationError("repos.yml must contain a repositories list")

    refs: List[RepositoryRef] = []
    for item in repositories:
        if isinstance(item, str):
            url = item
        elif isinstance(item, dict):
            url = item.get("url")
        else:
            raise ValidationError("each repository must be a URL string or mapping with url")
        if not isinstance(url, str) or not url.strip():
            raise ValidationError("repository url must be a non-empty string")
        refs.append(parse_repository_url(url.strip()))
    return refs


def parse_repos_sources(sources: ReposSources) -> List[RepositoryRef]:
    normalized_sources = normalize_repos_sources(sources)
    refs: List[RepositoryRef] = []
    seen: Dict[tuple[str, str], str] = {}
    duplicates: List[str] = []

    for source in normalized_sources:
        for ref in parse_repos(source):
            key = (ref.host, ref.slug.lower())
            if key in seen:
                duplicates.append(f"{ref.url} duplicates {seen[key]}")
            else:
                seen[key] = ref.url
                refs.append(ref)

    if duplicates:
        raise ValidationError("duplicate repository entries found: " + "; ".join(duplicates))
    return refs


def normalize_repos_sources(sources: ReposSources) -> List[str]:
    if isinstance(sources, str):
        values = [line.strip() for line in sources.splitlines()]
    else:
        values = [str(source).strip() for source in sources]
    values = [value for value in values if value]
    if not values:
        raise ValidationError("at least one repos.yml source is required")
    return values


def parse_repository_url(url: str) -> RepositoryRef:
    parsed = urlparse(url)
    host = parsed.netloc.lower()
    parts = [part for part in parsed.path.strip("/").split("/") if part]
    if host == "github.com" and len(parts) >= 2:
        return RepositoryRef(url=url, host="github", owner=parts[0], name=parts[1].removesuffix(".git"))
    if host == "gitlab.com" and len(parts) >= 2:
        return RepositoryRef(url=url, host="gitlab", owner="/".join(parts[:-1]), name=parts[-1].removesuffix(".git"))
    raise ValidationError(f"unsupported repository URL: {url}")


def parse_software_metadata(text: str) -> SoftwareMetadata:
    data = yaml.safe_load(text)
    if not isinstance(data, dict):
        raise ValidationError("software.yml must contain a mapping")

    missing = [field for field in REQUIRED_METADATA_FIELDS if not _non_empty_string(data.get(field))]
    if missing:
        raise ValidationError(f"missing required field(s): {', '.join(missing)}")

    webpage = data.get("webpage")
    if webpage is not None and not _non_empty_string(webpage):
        raise ValidationError("webpage must be a non-empty string when provided")

    return SoftwareMetadata(
        author_lab=data["author-lab"].strip(),
        name=data["name"].strip(),
        description=data["description"].strip(),
        webpage=webpage.strip() if isinstance(webpage, str) else None,
    )


def _non_empty_string(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())
