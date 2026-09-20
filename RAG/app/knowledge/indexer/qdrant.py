"""Qdrant collection lifecycle and document point writes."""
from collections.abc import Sequence
from uuid import UUID

from qdrant_client import models

from app.core.config import get_settings
from app.services.qdrant import get_qdrant_client, qdrant_retry


class QdrantIndexError(RuntimeError):
    pass


class QdrantDocumentIndex:
    def __init__(self) -> None:
        self.settings = get_settings()
        self.client = get_qdrant_client()
        self.collection = self.settings.qdrant_collection

    async def ensure_collection(self) -> None:
        if not await self.client.collection_exists(self.collection):
            await self.client.create_collection(
                collection_name=self.collection,
                vectors_config=models.VectorParams(
                    size=self.settings.embedding_dimensions,
                    distance=models.Distance.COSINE,
                ),
                on_disk_payload=True,
            )
        info = await self.client.get_collection(self.collection)
        vectors = info.config.params.vectors
        size = getattr(vectors, "size", None)
        if size is not None and size != self.settings.embedding_dimensions:
            raise QdrantIndexError(
                f"collection dimension is {size}, expected {self.settings.embedding_dimensions}"
            )
        schemas = {
            "document_id": models.PayloadSchemaType.KEYWORD,
            "document_version_id": models.PayloadSchemaType.KEYWORD,
            "document_type": models.PayloadSchemaType.KEYWORD,
            "academic_year": models.PayloadSchemaType.KEYWORD,
            "visibility": models.PayloadSchemaType.KEYWORD,
            "group_id": models.PayloadSchemaType.KEYWORD,
            "is_current": models.PayloadSchemaType.BOOL,
            "published_at": models.PayloadSchemaType.DATETIME,
        }
        for field, schema in schemas.items():
            if field not in info.payload_schema:
                await self.client.create_payload_index(
                    collection_name=self.collection, field_name=field,
                    field_schema=schema, wait=True,
                )

    async def mark_document_versions_stale(self, document_id: UUID) -> None:
        await qdrant_retry(lambda: self.client.set_payload(
            collection_name=self.collection,
            payload={"is_current": False},
            points=models.Filter(must=[models.FieldCondition(
                key="document_id", match=models.MatchValue(value=str(document_id))
            )]),
            wait=True,
        ))

    async def restore_previous_version(self, document_id: UUID, new_version_id: UUID) -> None:
        await qdrant_retry(lambda: self.client.set_payload(
            collection_name=self.collection,
            payload={"is_current": True},
            points=models.Filter(
                must=[models.FieldCondition(
                    key="document_id", match=models.MatchValue(value=str(document_id))
                )],
                must_not=[models.FieldCondition(
                    key="document_version_id", match=models.MatchValue(value=str(new_version_id))
                )],
            ),
            wait=True,
        ))

    async def upsert(self, points: Sequence[models.PointStruct]) -> None:
        await qdrant_retry(lambda: self.client.upsert(
            collection_name=self.collection, points=points, wait=True))

    async def delete(self, point_ids: Sequence[UUID]) -> None:
        if point_ids:
            await qdrant_retry(lambda: self.client.delete(
                collection_name=self.collection,
                points_selector=models.PointIdsList(points=list(point_ids)),
                wait=True,
            ))
