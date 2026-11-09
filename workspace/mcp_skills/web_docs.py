"""Search engine and markdown web downloader for fresh documentation.

Only http and https URLs are allowed, and private, loopback and link-local hosts are refused so
an agent cannot probe the Kaggle machine's internal network.
"""

from __future__ import annotations

import ipaddress
import socket
from urllib.parse import parse_qs, unquote, urlparse

import httpx
from bs4 import BeautifulSoup
from markdownify import markdownify

SKILL_NAME = "web_docs"
DESCRIPTION = (
    "Search the web (action 'search') or download a page as markdown (action 'fetch'). "
    "Use it for current library documentation. Always cite the returned URL."
)
PARAMETERS = {
    "type": "object",
    "properties": {
        "action": {"type": "string", "enum": ["search", "fetch"]},
        "query": {"type": "string", "description": "Search query, when action is search."},
        "url": {"type": "string", "description": "Page URL, when action is fetch."},
        "max_chars": {"type": "integer", "description": "Max characters returned, default 6000."},
    },
    "required": ["action"],
}
HEADERS = {"User-Agent": "KaggleAgent-Hybrid/0.1 (research agent)"}


def _is_public(host: str) -> bool:
    try:
        infos = socket.getaddrinfo(host, None)
    except socket.gaierror:
        return False
    for info in infos:
        ip = ipaddress.ip_address(info[4][0])
        if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved or ip.is_multicast:
            return False
    return True


def _search(query: str) -> str:
    resp = httpx.get("https://html.duckduckgo.com/html/", params={"q": query}, headers=HEADERS, timeout=20)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")
    results = []
    for link in soup.select("a.result__a")[:8]:
        href = link.get("href", "")
        target = parse_qs(urlparse(href).query).get("uddg", [href])[0]
        results.append(f"- {link.get_text(strip=True)}\n  {unquote(target)}")
    return "\n".join(results) or "no results"


def _fetch(url: str, max_chars: int) -> str:
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https") or not parsed.hostname:
        return "ERROR: only http and https URLs are allowed"
    if not _is_public(parsed.hostname):
        return "ERROR: host resolves to a non-public address and was refused"
    resp = httpx.get(url, headers=HEADERS, timeout=30, follow_redirects=True)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")
    for tag in soup(["script", "style", "nav", "footer"]):
        tag.decompose()
    body = markdownify(str(soup), heading_style="ATX", strip=["img"])
    body = "\n".join(line.rstrip() for line in body.splitlines() if line.strip())
    return f"Source: {resp.url}\n\n{body[:max_chars]}"


def run(action: str, query: str = "", url: str = "", max_chars: int = 6000) -> str:
    if action == "search":
        return _search(query) if query else "ERROR: query is required for search"
    if action == "fetch":
        return _fetch(url, max_chars) if url else "ERROR: url is required for fetch"
    return f"ERROR: unknown action '{action}'"
