"""Compatibility entrypoint; prefer `python -m scripts.index run`."""
from scripts.index import main
import asyncio

if __name__ == "__main__":
    asyncio.run(main())
