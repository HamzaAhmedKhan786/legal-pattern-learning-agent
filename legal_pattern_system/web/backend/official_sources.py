from __future__ import annotations

import re
from html import unescape
from typing import Any
from urllib.request import Request, urlopen


def fetch_official_sources(urls: list[str], *, allowed_domains: list[str], timeout_seconds: int = 15) -> dict[str, Any]:
    fetched = []
    rejected = []
    for url in urls:
        host = host_from_url(url)
        if not any(host == domain or host.endswith(f".{domain}") for domain in allowed_domains):
            rejected.append({"url": url, "host": host, "reason": "Domain is not on the official-source allowlist."})
            continue
        try:
            request = Request(url, headers={"User-Agent": "LegalPatternStudioOfficialSourceVerifier/0.1"})
            with urlopen(request, timeout=timeout_seconds) as response:
                content_type = response.headers.get("content-type", "")
                raw = response.read(250_000)
            text = raw.decode("utf-8", errors="ignore")
            fetched.append(
                {
                    "url": url,
                    "host": host,
                    "content_type": content_type,
                    "title": _title(text),
                    "snippet": _snippet(text),
                }
            )
        except Exception as exc:  # pragma: no cover - network-dependent connector
            rejected.append({"url": url, "host": host, "reason": str(exc)})
    return {"fetched": fetched, "rejected": rejected}


def host_from_url(url: str) -> str:
    value = url.strip().lower()
    value = value.removeprefix("https://").removeprefix("http://")
    return value.split("/", 1)[0].split(":", 1)[0]


def _title(html: str) -> str:
    match = re.search(r"<title[^>]*>(.*?)</title>", html, flags=re.IGNORECASE | re.DOTALL)
    return unescape(re.sub(r"\s+", " ", match.group(1)).strip()) if match else ""


def _snippet(html: str) -> str:
    text = re.sub(r"<script.*?</script>|<style.*?</style>", " ", html, flags=re.IGNORECASE | re.DOTALL)
    text = re.sub(r"<[^>]+>", " ", text)
    text = unescape(re.sub(r"\s+", " ", text).strip())
    return text[:1200]
