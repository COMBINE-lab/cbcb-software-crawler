import json
import shutil
from importlib import resources
from pathlib import Path
from string import Template
from typing import Iterable, List

from .models import CrawlReport, SoftwareEntry


def render_bundle(entries: List[SoftwareEntry], report: CrawlReport, out_dir: str) -> Path:
    output = Path(out_dir)
    output.mkdir(parents=True, exist_ok=True)
    assets_dir = output / "assets"
    assets_dir.mkdir(exist_ok=True)

    software_json = [entry.to_json() for entry in entries]
    report_json = report.to_json()
    (output / "software.json").write_text(json.dumps(software_json, indent=2), encoding="utf-8")
    (output / "report.json").write_text(json.dumps(report_json, indent=2), encoding="utf-8")

    _copy_asset("catalog.css", assets_dir / "catalog.css")
    _copy_asset("catalog.js", assets_dir / "catalog.js")

    table_html = render_table_fragment(entries, report)
    index_template = _read_template("index.html")
    report_template = _read_template("report.html")

    (output / "index.html").write_text(
        Template(index_template).safe_substitute(
            active_years=report.active_years,
            generated_at=report.generated_at.date().isoformat(),
            table_fragment=table_html,
        ),
        encoding="utf-8",
    )
    (output / "drupal-fragment.html").write_text(render_drupal_fragment(table_html), encoding="utf-8")
    (output / "report.html").write_text(
        Template(report_template).safe_substitute(
            generated_at=report.generated_at.isoformat(),
            source=report.source,
            valid_count=report.valid_count,
            skipped_rows=_render_skipped_rows(report),
        ),
        encoding="utf-8",
    )
    return output


def render_table_fragment(entries: Iterable[SoftwareEntry], report: CrawlReport) -> str:
    rows = "\n".join(_render_entry_row(entry) for entry in entries)
    if not rows:
        rows = '<tr><td colspan="6">No valid software metadata was found.</td></tr>'
    return Template(_read_template("table_fragment.html")).safe_substitute(
        active_years=report.active_years,
        generated_at=report.generated_at.date().isoformat(),
        rows=rows,
        total=report.valid_count,
    )


def render_drupal_fragment(table_html: str) -> str:
    css = _read_asset("drupal-fragment.css")
    js = _read_asset("catalog.js")
    return (
        "<!-- CBCB software catalog fragment: paste into a Drupal HTML/full-HTML block. -->\n"
        "<style>\n"
        f"{css}\n"
        "</style>\n"
        '<div class="cbcb-software-embed">\n'
        f"{table_html}\n"
        "</div>\n"
        "<script>\n"
        f"{js}\n"
        "</script>\n"
    )


def _render_entry_row(entry: SoftwareEntry) -> str:
    webpage = f'<a href="{_escape(entry.webpage)}">Website</a>' if entry.webpage else ""
    version = _escape(entry.latest_version or "")
    last_edited = entry.last_edited.date().isoformat() if entry.last_edited else ""
    return (
        f'<tr data-active="{str(entry.active).lower()}">'
        f"<td>{_escape(entry.name)}</td>"
        f"<td>{_escape(entry.author_lab)}</td>"
        f"<td>{_escape(entry.description)}</td>"
        f'<td><a href="{_escape(entry.repository)}">{_escape(entry.host.title())}</a></td>'
        f"<td>{version}</td>"
        f"<td>{last_edited}</td>"
        f"<td>{webpage}</td>"
        "</tr>"
    )


def _render_skipped_rows(report: CrawlReport) -> str:
    if not report.skipped:
        return '<tr><td colspan="3">No repositories were skipped.</td></tr>'
    return "\n".join(
        f"<tr><td>{_escape(issue.repository)}</td><td>{_escape(issue.reason)}</td><td>{_escape(issue.detail or '')}</td></tr>"
        for issue in report.skipped
    )


def _read_template(name: str) -> str:
    return resources.files("cbcb_software_crawler").joinpath("templates", name).read_text(encoding="utf-8")


def _copy_asset(name: str, dest: Path) -> None:
    source = resources.files("cbcb_software_crawler").joinpath("assets", name)
    with resources.as_file(source) as source_path:
        shutil.copyfile(source_path, dest)


def _read_asset(name: str) -> str:
    return resources.files("cbcb_software_crawler").joinpath("assets", name).read_text(encoding="utf-8")


def _escape(value: str) -> str:
    return (
        value.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
        .replace("'", "&#x27;")
    )
