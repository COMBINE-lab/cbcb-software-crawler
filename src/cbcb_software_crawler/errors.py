class CrawlerError(Exception):
    """Base error for expected crawler failures."""


class ValidationError(CrawlerError):
    """Raised when input metadata is invalid."""


class HostError(CrawlerError):
    """Raised when a repository host cannot be reached or parsed."""
