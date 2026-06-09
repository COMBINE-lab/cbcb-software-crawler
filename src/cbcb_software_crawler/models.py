from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


@dataclass(frozen=True)
class RepositoryRef:
    url: str
    host: str
    owner: str
    name: str

    @property
    def slug(self) -> str:
        return f"{self.owner}/{self.name}"


@dataclass
class SoftwareMetadata:
    author_lab: str
    name: str
    description: str
    webpage: Optional[str] = None


@dataclass
class RepositoryFacts:
    repo_url: str
    host: str
    latest_version: Optional[str] = None
    last_edited: Optional[datetime] = None


@dataclass
class SoftwareEntry:
    author_lab: str
    name: str
    description: str
    webpage: Optional[str]
    repository: str
    host: str
    latest_version: Optional[str]
    last_edited: Optional[datetime]
    active: bool

    def to_json(self) -> Dict[str, Any]:
        data = asdict(self)
        data["last_edited"] = self.last_edited.date().isoformat() if self.last_edited else None
        return data


@dataclass
class CrawlIssue:
    repository: str
    reason: str
    detail: Optional[str] = None

    def to_json(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class CrawlReport:
    generated_at: datetime
    source: str
    active_years: int
    valid_count: int = 0
    skipped: List[CrawlIssue] = field(default_factory=list)

    def to_json(self) -> Dict[str, Any]:
        return {
            "generated_at": self.generated_at.astimezone(timezone.utc).isoformat(),
            "source": self.source,
            "active_years": self.active_years,
            "valid_count": self.valid_count,
            "skipped": [issue.to_json() for issue in self.skipped],
        }
