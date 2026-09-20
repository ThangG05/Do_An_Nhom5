"""Ensure the configured Qdrant collection is compatible with embeddings."""
import asyncio

from app.knowledge.indexer.qdrant import QdrantDocumentIndex, QdrantIndexError
from app.services.qdrant import close_qdrant


async def main() -> None:
    try:
        await QdrantDocumentIndex().ensure_collection()
        print("qdrant_collection=ok")
    except QdrantIndexError:
        print("qdrant_collection=error (dimension_mismatch)")
        raise SystemExit(1) from None
    except Exception:
        print("qdrant_collection=error (provider_unavailable)")
        raise SystemExit(1) from None
    finally:
        await close_qdrant()


if __name__ == "__main__":
    asyncio.run(main())
