from datetime import datetime, timezone
from pathlib import Path

from cbcb_software_crawler.crawler import crawl
from cbcb_software_crawler.models import RepositoryFacts


class FakeClient:
    def __init__(self, metadata: str, facts: RepositoryFacts) -> None:
        self.metadata = metadata
        self.facts = facts

    def fetch_metadata_file(self, ref, path="software.yml") -> str:
        return self.metadata

    def fetch_repository_facts(self, ref) -> RepositoryFacts:
        return self.facts


def test_crawl_enriches_and_marks_active(tmp_path: Path) -> None:
    source = tmp_path / "repos.yml"
    source.write_text("repositories:\n  - url: https://github.com/umd/tool\n", encoding="utf-8")
    metadata = "author-lab: Lab\nname: Tool\ndescription: Useful.\n"
    facts = RepositoryFacts(
        repo_url="https://github.com/umd/tool",
        host="github",
        latest_version="v1.2.3",
        last_edited=datetime(2026, 1, 1, tzinfo=timezone.utc),
    )

    entries, report = crawl(
        str(source),
        active_years=2,
        now=datetime(2026, 6, 5, tzinfo=timezone.utc),
        client_factory=lambda ref: FakeClient(metadata, facts),
    )

    assert report.valid_count == 1
    assert not report.skipped
    assert entries[0].latest_version == "v1.2.3"
    assert entries[0].active is True


def test_crawl_accepts_multiple_repo_sources(tmp_path: Path) -> None:
    first = tmp_path / "first.yml"
    second = tmp_path / "second.yml"
    first.write_text("repositories:\n  - url: https://github.com/umd/one\n", encoding="utf-8")
    second.write_text("repositories:\n  - url: https://github.com/umd/two\n", encoding="utf-8")
    metadata = "author-lab: Lab\nname: Tool\ndescription: Useful.\n"
    facts = RepositoryFacts(
        repo_url="https://github.com/umd/tool",
        host="github",
        latest_version="v1",
        last_edited=datetime(2026, 1, 1, tzinfo=timezone.utc),
    )

    entries, report = crawl(
        [str(first), str(second)],
        now=datetime(2026, 6, 5, tzinfo=timezone.utc),
        client_factory=lambda ref: FakeClient(metadata, facts),
    )

    assert len(entries) == 2
    assert report.source == f"{first}\n{second}"


def test_crawl_keeps_valid_inactive_entries(tmp_path: Path) -> None:
    source = tmp_path / "repos.yml"
    source.write_text("repositories:\n  - url: https://github.com/umd/old-tool\n", encoding="utf-8")
    metadata = "author-lab: Lab\nname: Old Tool\ndescription: Useful.\n"
    facts = RepositoryFacts(
        repo_url="https://github.com/umd/old-tool",
        host="github",
        latest_version=None,
        last_edited=datetime(2020, 1, 1, tzinfo=timezone.utc),
    )

    entries, report = crawl(
        str(source),
        active_years=2,
        now=datetime(2026, 6, 5, tzinfo=timezone.utc),
        client_factory=lambda ref: FakeClient(metadata, facts),
    )

    assert report.valid_count == 1
    assert entries[0].active is False


def test_crawl_skips_invalid_metadata(tmp_path: Path) -> None:
    source = tmp_path / "repos.yml"
    source.write_text("repositories:\n  - url: https://github.com/umd/bad-tool\n", encoding="utf-8")
    facts = RepositoryFacts(repo_url="https://github.com/umd/bad-tool", host="github")

    entries, report = crawl(
        str(source),
        client_factory=lambda ref: FakeClient("name: Bad\n", facts),
    )

    assert entries == []
    assert report.skipped[0].reason == "ValidationError"
