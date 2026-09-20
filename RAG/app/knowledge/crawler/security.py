import asyncio
import hashlib
import ipaddress
from urllib.parse import parse_qsl, quote, urlencode, urljoin, urlsplit, urlunsplit


class UnsafeURL(ValueError):
    pass


_TRACKING = {"fbclid", "gclid", "mc_cid", "mc_eid"}


def canonicalize_url(url: str, base_url: str | None = None) -> str:
    absolute = urljoin(base_url, url) if base_url else url
    parts = urlsplit(absolute.strip())
    if parts.scheme.lower() != "https" or not parts.hostname or parts.username or parts.password:
        raise UnsafeURL("only credential-free HTTPS URLs are accepted")
    if parts.port not in (None, 443):
        raise UnsafeURL("non-standard ports are not accepted")
    host = parts.hostname.rstrip(".").encode("idna").decode("ascii").lower()
    path = quote(parts.path or "/", safe="/%:@!$&'()*+,;=-._~")
    query = [(k, v) for k, v in parse_qsl(parts.query, keep_blank_values=True)
             if k.lower() not in _TRACKING and not k.lower().startswith("utm_")]
    return urlunsplit(("https", host, path, urlencode(sorted(query)), ""))


def url_hash(url: str) -> str:
    return hashlib.sha256(url.encode("utf-8")).hexdigest()


def is_in_scope(url: str, allowed_domains: list[str], allowed_path_prefixes: list[str]) -> bool:
    parts = urlsplit(url)
    host = (parts.hostname or "").lower().rstrip(".")
    domains = [item.lower().rstrip(".") for item in allowed_domains]
    domain_ok = any(host == domain or host.endswith("." + domain) for domain in domains)
    path_ok = not allowed_path_prefixes or any(parts.path.startswith(prefix) for prefix in allowed_path_prefixes)
    return domain_ok and path_ok


async def validate_public_url(url: str) -> None:
    host = urlsplit(url).hostname
    if not host:
        raise UnsafeURL("URL has no hostname")
    loop = asyncio.get_running_loop()
    try:
        records = await loop.getaddrinfo(host, 443, type=0)
    except OSError as exc:
        raise UnsafeURL("hostname cannot be resolved") from exc
    for record in records:
        address = ipaddress.ip_address(record[4][0])
        if not address.is_global:
            raise UnsafeURL("URL resolves to a non-public address")
