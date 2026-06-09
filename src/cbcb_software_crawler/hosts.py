import json
import os
from datetime import datetime, timezone
from typing import Any, Dict, Iterable, List, Optional
from urllib.parse import quote

from .errors import HostError
from .http import fetch_text
from .models import RepositoryFacts, RepositoryRef


class HostClient:
    def fetch_metadata_file(self, ref: RepositoryRef, path: str = "software.yml") -> str:
        raise NotImplementedError

    def fetch_repository_facts(self, ref: RepositoryRef) -> RepositoryFacts:
        raise NotImplementedError


class GitHubClient(HostClient):
    api_base = "https://api.github.com"
    raw_base = "https://raw.githubusercontent.com"

    def __init__(self, token: Optional[str] = None) -> None:
        self.token = token or os.getenv("GITHUB_TOKEN")

    def fetch_metadata_file(self, ref: RepositoryRef, path: str = "software.yml") -> str:
        repo = self._get_json(f"/repos/{ref.owner}/{ref.name}")
        default_branch = repo.get("default_branch") or "main"
        raw_url = f"{self.raw_base}/{ref.owner}/{ref.name}/{default_branch}/{path}"
        return fetch_text(raw_url, headers=self._headers(raw=False))

    def fetch_repository_facts(self, ref: RepositoryRef) -> RepositoryFacts:
        repo = self._get_json(f"/repos/{ref.owner}/{ref.name}")
        latest_version = self._latest_release(ref) or self._latest_tag(ref)
        last_edited = parse_datetime(repo.get("pushed_at"))
        if last_edited is None:
            last_edited = self._latest_commit_date(ref, repo.get("default_branch") or "main")
        return RepositoryFacts(
            repo_url=repo.get("html_url") or ref.url,
            host="github",
            latest_version=latest_version,
            last_edited=last_edited,
        )

    def _latest_release(self, ref: RepositoryRef) -> Optional[str]:
        try:
            release = self._get_json(f"/repos/{ref.owner}/{ref.name}/releases/latest")
        except HostError:
            return None
        return release.get("tag_name") or release.get("name")

    def _latest_tag(self, ref: RepositoryRef) -> Optional[str]:
        tags = self._get_json(f"/repos/{ref.owner}/{ref.name}/tags?per_page=1")
        if isinstance(tags, list) and tags:
            return tags[0].get("name")
        return None

    def _latest_commit_date(self, ref: RepositoryRef, branch: str) -> Optional[datetime]:
        commits = self._get_json(f"/repos/{ref.owner}/{ref.name}/commits?sha={quote(branch)}&per_page=1")
        if isinstance(commits, list) and commits:
            commit = commits[0].get("commit", {})
            committer = commit.get("committer", {})
            return parse_datetime(committer.get("date"))
        return None

    def _get_json(self, path: str) -> Any:
        return json.loads(fetch_text(f"{self.api_base}{path}", headers=self._headers()))

    def _headers(self, raw: bool = False) -> Dict[str, str]:
        headers = {"User-Agent": "cbcb-software-crawler"}
        if not raw:
            headers["Accept"] = "application/vnd.github+json"
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        return headers


class GitLabClient(HostClient):
    api_base = "https://gitlab.com/api/v4"

    def __init__(self, token: Optional[str] = None) -> None:
        self.token = token or os.getenv("GITLAB_TOKEN")

    def fetch_metadata_file(self, ref: RepositoryRef, path: str = "software.yml") -> str:
        project = self._project(ref)
        default_branch = project.get("default_branch") or "main"
        project_id = quote(ref.slug, safe="")
        file_path = quote(path, safe="")
        endpoint = f"/projects/{project_id}/repository/files/{file_path}/raw?ref={quote(default_branch)}"
        return fetch_text(f"{self.api_base}{endpoint}", headers=self._headers())

    def fetch_repository_facts(self, ref: RepositoryRef) -> RepositoryFacts:
        project = self._project(ref)
        latest_version = self._latest_release(ref) or self._latest_tag(ref)
        last_edited = parse_datetime(project.get("last_activity_at"))
        if last_edited is None:
            last_edited = self._latest_commit_date(ref, project.get("default_branch") or "main")
        return RepositoryFacts(
            repo_url=project.get("web_url") or ref.url,
            host="gitlab",
            latest_version=latest_version,
            last_edited=last_edited,
        )

    def _project(self, ref: RepositoryRef) -> Dict[str, Any]:
        return self._get_json(f"/projects/{quote(ref.slug, safe='')}")

    def _latest_release(self, ref: RepositoryRef) -> Optional[str]:
        try:
            releases = self._get_json(f"/projects/{quote(ref.slug, safe='')}/releases?per_page=1")
        except HostError:
            return None
        if isinstance(releases, list) and releases:
            return releases[0].get("tag_name") or releases[0].get("name")
        return None

    def _latest_tag(self, ref: RepositoryRef) -> Optional[str]:
        tags = self._get_json(f"/projects/{quote(ref.slug, safe='')}/repository/tags?per_page=1")
        if isinstance(tags, list) and tags:
            return tags[0].get("name")
        return None

    def _latest_commit_date(self, ref: RepositoryRef, branch: str) -> Optional[datetime]:
        commits = self._get_json(
            f"/projects/{quote(ref.slug, safe='')}/repository/commits?ref_name={quote(branch)}&per_page=1"
        )
        if isinstance(commits, list) and commits:
            return parse_datetime(commits[0].get("committed_date"))
        return None

    def _get_json(self, path: str) -> Any:
        return json.loads(fetch_text(f"{self.api_base}{path}", headers=self._headers()))

    def _headers(self) -> Dict[str, str]:
        headers = {"User-Agent": "cbcb-software-crawler"}
        if self.token:
            headers["PRIVATE-TOKEN"] = self.token
        return headers


def client_for(ref: RepositoryRef) -> HostClient:
    if ref.host == "github":
        return GitHubClient()
    if ref.host == "gitlab":
        return GitLabClient()
    raise HostError(f"unsupported host: {ref.host}")


def parse_datetime(value: Optional[str]) -> Optional[datetime]:
    if not value:
        return None
    normalized = value.replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)
