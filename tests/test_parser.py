from pathlib import Path

import pytest

from cbcb_software_crawler.errors import ValidationError
from cbcb_software_crawler.parser import parse_repository_url, parse_repos, parse_repos_sources, parse_software_metadata


def test_parse_repos_accepts_mapping_entries(tmp_path: Path) -> None:
    source = tmp_path / "repos.yml"
    source.write_text("repositories:\n  - url: https://github.com/umd/tool\n", encoding="utf-8")

    refs = parse_repos(str(source))

    assert refs[0].host == "github"
    assert refs[0].slug == "umd/tool"


def test_parse_repos_sources_merges_multiple_files(tmp_path: Path) -> None:
    first = tmp_path / "first.yml"
    second = tmp_path / "second.yml"
    first.write_text("repositories:\n  - url: https://github.com/umd/one\n", encoding="utf-8")
    second.write_text("repositories:\n  - url: https://gitlab.com/group/two\n", encoding="utf-8")

    refs = parse_repos_sources([str(first), str(second)])

    assert [ref.slug for ref in refs] == ["umd/one", "group/two"]


def test_parse_repos_sources_rejects_duplicates(tmp_path: Path) -> None:
    first = tmp_path / "first.yml"
    second = tmp_path / "second.yml"
    first.write_text("repositories:\n  - url: https://github.com/umd/tool\n", encoding="utf-8")
    second.write_text("repositories:\n  - url: https://github.com/umd/tool.git\n", encoding="utf-8")

    with pytest.raises(ValidationError, match="duplicate repository"):
        parse_repos_sources([str(first), str(second)])


def test_parse_repository_url_accepts_gitlab_groups() -> None:
    ref = parse_repository_url("https://gitlab.com/group/subgroup/tool.git")

    assert ref.host == "gitlab"
    assert ref.owner == "group/subgroup"
    assert ref.name == "tool"


def test_parse_software_metadata_validates_required_fields() -> None:
    with pytest.raises(ValidationError, match="missing required"):
        parse_software_metadata("name: Tool\n")


def test_parse_software_metadata_maps_author_lab() -> None:
    metadata = parse_software_metadata(
        "author-lab: Lab\nname: Tool\ndescription: Useful.\nwebpage: https://example.org\n"
    )

    assert metadata.author_lab == "Lab"
    assert metadata.webpage == "https://example.org"
