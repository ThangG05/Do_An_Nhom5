import argparse
import asyncio
import sys
from urllib.parse import urlsplit

from app.knowledge.crawler.extractors import extract_document
from app.knowledge.crawler.fetcher import SafeFetcher


async def main(url: str) -> None:
    host = urlsplit(url).hostname
    if not host: raise ValueError("invalid URL")
    fetcher = SafeFetcher([host], [])
    try:
        fetched = await fetcher.fetch(url)
        extracted = extract_document(fetched.body, fetched.content_type, fetched.url)
        print(f"crawler=ok status={fetched.status_code} bytes={len(fetched.body)} text_chars={len(extracted.content)} links={len(extracted.links)}")
        print(f"title={extracted.title[:200]}")
    finally:
        await fetcher.close()


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"): sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(); parser.add_argument("url")
    asyncio.run(main(parser.parse_args().url))
