from typing import Dict, Optional
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from .errors import HostError


def fetch_text(url: str, headers: Optional[Dict[str, str]] = None, timeout: int = 30) -> str:
    request = Request(url, headers=headers or {})
    try:
        with urlopen(request, timeout=timeout) as response:
            charset = response.headers.get_content_charset() or "utf-8"
            return response.read().decode(charset)
    except HTTPError as exc:
        raise HostError(f"HTTP {exc.code} fetching {url}") from exc
    except URLError as exc:
        raise HostError(f"Could not fetch {url}: {exc.reason}") from exc
