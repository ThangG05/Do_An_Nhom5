"""Bounded HTTP load smoke test; never logs credentials or question bodies."""
import argparse
import asyncio
import os
from statistics import mean
from time import perf_counter

import httpx
from app.core.config import get_settings


async def main() -> None:
    parser = argparse.ArgumentParser(description="Run a bounded RAG API load smoke test")
    parser.add_argument("--url", default="http://localhost:8000/api/v1/internal/rag/ask")
    parser.add_argument("--requests", type=int, default=10, choices=range(1, 201), metavar="1..200")
    parser.add_argument("--concurrency", type=int, default=2, choices=range(1, 21), metavar="1..20")
    parser.add_argument("--question", default="Chuẩn đầu ra ngoại ngữ VSTEP như thế nào?")
    parser.add_argument("--timeout", type=float, default=180)
    args = parser.parse_args()
    api_key = os.getenv("INTERNAL_API_KEY") or get_settings().internal_api_key
    if not api_key:
        raise SystemExit("INTERNAL_API_KEY is required")
    semaphore = asyncio.Semaphore(args.concurrency)
    latencies: list[float] = []
    statuses: list[int] = []

    async with httpx.AsyncClient(timeout=args.timeout) as client:
        async def request_once() -> None:
            async with semaphore:
                started = perf_counter()
                try:
                    response = await client.post(args.url, json={"question": args.question},
                                                 headers={"X-Internal-API-Key": api_key})
                    statuses.append(response.status_code)
                except httpx.HTTPError:
                    statuses.append(0)
                finally:
                    latencies.append((perf_counter() - started) * 1000)

        await asyncio.gather(*(request_once() for _ in range(args.requests)))
    ordered = sorted(latencies)
    percentile = lambda p: ordered[min(round((len(ordered) - 1) * p), len(ordered) - 1)]
    successes = sum(status == 200 for status in statuses)
    print(f"requests={len(statuses)} successes={successes} errors={len(statuses)-successes} "
          f"mean_ms={mean(latencies):.0f} p50_ms={percentile(.50):.0f} p95_ms={percentile(.95):.0f} "
          f"max_ms={max(latencies):.0f}")
    if successes != len(statuses):
        raise SystemExit(1)


if __name__ == "__main__":
    asyncio.run(main())
