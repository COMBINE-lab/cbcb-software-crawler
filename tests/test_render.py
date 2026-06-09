import json
from datetime import datetime, timezone
from pathlib import Path

from cbcb_software_crawler.models import CrawlReport, SoftwareEntry
from cbcb_software_crawler.render import render_bundle


def test_render_bundle_writes_static_outputs(tmp_path: Path) -> None:
    entry = SoftwareEntry(
        author_lab="Lab",
        name="Tool",
        description="Useful.",
        webpage=None,
        repository="https://github.com/umd/tool",
        host="github",
        latest_version="v1",
        last_edited=datetime(2026, 1, 1, tzinfo=timezone.utc),
        active=True,
    )
    report = CrawlReport(
        generated_at=datetime(2026, 6, 5, tzinfo=timezone.utc),
        source="repos.yml",
        active_years=2,
        valid_count=1,
    )

    render_bundle([entry], report, str(tmp_path))

    assert (tmp_path / "index.html").exists()
    assert (tmp_path / "drupal-fragment.html").exists()
    drupal_fragment = (tmp_path / "drupal-fragment.html").read_text(encoding="utf-8")
    assert "<style>" in drupal_fragment
    assert "<script>" in drupal_fragment
    assert "cbcb-software-embed" in drupal_fragment
    assert ".software-catalog" in drupal_fragment
    data = json.loads((tmp_path / "software.json").read_text(encoding="utf-8"))
    assert data[0]["name"] == "Tool"
