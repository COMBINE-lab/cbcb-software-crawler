from datetime import datetime, timedelta, timezone
from typing import Callable, Dict, List, Optional

from .errors import CrawlerError, ValidationError
from .hosts import HostClient, client_for
from .models import CrawlIssue, CrawlReport, SoftwareEntry
from .parser import ReposSources, normalize_repos_sources, parse_repos_sources, parse_software_metadata

ClientFactory = Callable[[object], HostClient]


def crawl(
    repos_source: ReposSources,
    active_years: int = 2,
    client_factory: Optional[ClientFactory] = None,
    now: Optional[datetime] = None,
) -> tuple[List[SoftwareEntry], CrawlReport]:
    if active_years < 0:
        raise ValidationError("active_years must be zero or greater")

    generated_at = now or datetime.now(timezone.utc)
    cutoff = generated_at - timedelta(days=active_years * 365)
    source_list = normalize_repos_sources(repos_source)
    refs = parse_repos_sources(source_list)
    entries: List[SoftwareEntry] = []
    report = CrawlReport(generated_at=generated_at, source="\n".join(source_list), active_years=active_years)
    factory = client_factory or client_for

    for ref in refs:
        try:
            client = factory(ref)
            metadata_text = client.fetch_metadata_file(ref)
            metadata = parse_software_metadata(metadata_text)
            facts = client.fetch_repository_facts(ref)
            active = bool(facts.last_edited and facts.last_edited >= cutoff)
            entries.append(
                SoftwareEntry(
                    author_lab=metadata.author_lab,
                    name=metadata.name,
                    description=metadata.description,
                    webpage=metadata.webpage,
                    repository=facts.repo_url,
                    host=facts.host,
                    latest_version=facts.latest_version,
                    last_edited=facts.last_edited,
                    active=active,
                )
            )
        except CrawlerError as exc:
            report.skipped.append(CrawlIssue(repository=ref.url, reason=exc.__class__.__name__, detail=str(exc)))
        except Exception as exc:
            report.skipped.append(CrawlIssue(repository=ref.url, reason=exc.__class__.__name__, detail=str(exc)))

    entries.sort(key=lambda entry: (entry.author_lab.lower(), entry.name.lower()))
    report.valid_count = len(entries)
    return entries, report
