import argparse
from pathlib import Path

from .crawler import crawl
from .render import render_bundle


def main() -> None:
    parser = argparse.ArgumentParser(prog="cbcb-software-crawler")
    subparsers = parser.add_subparsers(dest="command", required=True)

    crawl_parser = subparsers.add_parser("crawl", help="Crawl repositories and generate a static catalog")
    crawl_parser.add_argument(
        "--repos",
        required=True,
        nargs="+",
        help="One or more local paths or URLs to repos.yml files",
    )
    crawl_parser.add_argument("--out", default="dist", help="Output directory")
    crawl_parser.add_argument("--active-years", type=int, default=2, help="Activity window for default display")

    args = parser.parse_args()
    if args.command == "crawl":
        entries, report = crawl(args.repos, active_years=args.active_years)
        output = render_bundle(entries, report, args.out)
        print(f"Wrote {report.valid_count} valid software entries to {Path(output).resolve()}")
        if report.skipped:
            print(f"Skipped {len(report.skipped)} repositories; see {Path(output, 'report.html').resolve()}")
