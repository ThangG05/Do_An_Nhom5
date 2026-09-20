import argparse
import asyncio
from collections import Counter
import sys
from urllib.parse import urlsplit

from app.knowledge.crawler.extractors import extract_document
from app.knowledge.crawler.fetcher import SafeFetcher
from app.knowledge.crawler.security import canonicalize_url
from bs4 import BeautifulSoup


# Windows terminals may still default to cp1252 even though official HVNH file
# names contain Vietnamese characters. Keep this diagnostic usable there.
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")


async def main(url: str, limit: int, needle: str | None) -> None:
    seed = canonicalize_url(url)
    host = urlsplit(seed).hostname
    if host is None:
        raise ValueError("URL has no hostname")
    fetcher = SafeFetcher([host], [])
    try:
        fetched = await fetcher.fetch(seed)
        if needle and fetched.content_type == "text/html":
            soup = BeautifulSoup(fetched.body, "html.parser")
            node = next((item for item in soup.find_all(string=True) if needle.casefold() in str(item).casefold()), None)
            if node:
                current = node.parent
                for _ in range(8):
                    if current is None:
                        break
                    print(f"ancestor={current.name} id={current.get('id')} class={' '.join(current.get('class', []))}")
                    current = current.parent
        if fetched.content_type == "text/html":
            soup = BeautifulSoup(fetched.body, "html.parser")
            embedded = []
            for selector, attribute in (("img[src]", "src"), ("iframe[src]", "src"),
                                        ("object[data]", "data"), ("embed[src]", "src")):
                for node in soup.select(selector):
                    try:
                        embedded.append(canonicalize_url(node.get(attribute), fetched.url))
                    except Exception:
                        continue
            if embedded:
                print("embedded:")
                for item in dict.fromkeys(embedded):
                    print(item)
        extracted = extract_document(fetched.body, fetched.content_type, fetched.url, allow_short=True)
        links = sorted(set(extracted.links))
        paths = [urlsplit(link).path for link in links if urlsplit(link).hostname == host]
        prefixes = Counter("/" + "/".join(path.strip("/").split("/")[:3]) for path in paths)
        print(f"url={fetched.url} links={len(links)}")
        for prefix, count in prefixes.most_common(20):
            print(f"prefix={prefix} count={count}")
        print("candidates:")
        candidates = [
            link for link in links
            if any(token in urlsplit(link).path.lower() for token in
                   (".pdf", ".doc", ".docx", ".xls", ".xlsx", "/detail/", ".html"))
        ]
        for link in candidates[:limit]:
            print(link)
    finally:
        await fetcher.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Inspect links from one approved public seed without saving data")
    parser.add_argument("url")
    parser.add_argument("--limit", type=int, default=30)
    parser.add_argument("--needle")
    args = parser.parse_args()
    asyncio.run(main(args.url, args.limit, args.needle))
