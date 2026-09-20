import argparse
import asyncio
import sys
from uuid import UUID

from sqlalchemy import select

from app.db.session import AsyncSessionLocal, dispose_engine
from app.models.enums import AIDocumentStatus
from app.models.rag import AIDocument, AIDocumentVersion
from app.llm.security import injection_signal_spans


async def list_items(args) -> None:
    async with AsyncSessionLocal() as session:
        rows = (await session.execute(
            select(AIDocumentVersion, AIDocument)
            .join(AIDocument, AIDocument.id == AIDocumentVersion.document_id)
            .where(AIDocumentVersion.metadata_["security_review"].astext == "QUARANTINED")
            .order_by(AIDocumentVersion.created_at.desc()).limit(args.limit)
        )).all()
    for version, document in rows:
        print(f"version_id={version.id} reason={(version.metadata_ or {}).get('security_reason', '-')} "
              f"title={document.title}\nsource={version.source_url or '-'}")
    print(f"quarantined={len(rows)}")


async def approve(args) -> None:
    async with AsyncSessionLocal() as session:
        version = await session.get(AIDocumentVersion, UUID(args.version_id))
        if version is None:
            raise ValueError("document version not found")
        if (version.metadata_ or {}).get("security_review") != "QUARANTINED":
            raise ValueError("document version is not quarantined")
        version.metadata_ = {**dict(version.metadata_ or {}), "security_review": "APPROVED"}
        version.status = AIDocumentStatus.PENDING
        version.error_message = None
        await session.commit()
        print(f"version_id={version.id} status=PENDING security_review=APPROVED")


async def dismiss(args) -> None:
    async with AsyncSessionLocal() as session:
        version = await session.get(AIDocumentVersion, UUID(args.version_id))
        if version is None:
            raise ValueError("document version not found")
        if (version.metadata_ or {}).get("security_review") != "QUARANTINED":
            raise ValueError("document version is not quarantined")
        version.metadata_ = {**dict(version.metadata_ or {}),
                             "security_review": "DISMISSED",
                             "security_resolution": args.reason}
        version.status = AIDocumentStatus.ARCHIVED
        version.error_message = None
        await session.commit()
        print(f"version_id={version.id} status=ARCHIVED security_review=DISMISSED")


async def adopt_failed(_) -> None:
    async with AsyncSessionLocal() as session:
        versions = list((await session.scalars(select(AIDocumentVersion).where(
            AIDocumentVersion.status == AIDocumentStatus.FAILED,
            AIDocumentVersion.error_message == "PromptSecurityError",
        ))).all())
        for version in versions:
            if (version.metadata_ or {}).get("security_review") is None:
                version.metadata_ = {
                    **dict(version.metadata_ or {}),
                    "security_review": "QUARANTINED",
                    "security_reason": "legacy_context_prompt_injection",
                }
        await session.commit()
    print(f"adopted={len(versions)}")


async def inspect_item(args) -> None:
    async with AsyncSessionLocal() as session:
        row = (await session.execute(
            select(AIDocumentVersion, AIDocument)
            .join(AIDocument, AIDocument.id == AIDocumentVersion.document_id)
            .where(AIDocumentVersion.id == UUID(args.version_id))
        )).one_or_none()
    if row is None:
        raise ValueError("document version not found")
    version, document = row
    content = version.raw_content or ""
    signals = injection_signal_spans(content)
    print(f"version_id={version.id} title={document.title} signals={len(signals)}")
    for name, start, end in signals[:args.limit]:
        excerpt = " ".join(content[max(0, start - 100):min(len(content), end + 100)].split())
        print(f"signal={name} offset={start}:{end} excerpt={excerpt[:500]}")


async def main() -> None:
    parser = argparse.ArgumentParser(description="Review prompt-injection quarantine")
    commands = parser.add_subparsers(dest="command", required=True)
    listing = commands.add_parser("list"); listing.add_argument("--limit", type=int, default=50)
    listing.set_defaults(handler=list_items)
    approval = commands.add_parser("approve"); approval.add_argument("--version-id", required=True)
    approval.set_defaults(handler=approve)
    dismissal = commands.add_parser("dismiss")
    dismissal.add_argument("--version-id", required=True)
    dismissal.add_argument("--reason", default="superseded_false_positive")
    dismissal.set_defaults(handler=dismiss)
    adopt = commands.add_parser("adopt-failed"); adopt.set_defaults(handler=adopt_failed)
    inspection = commands.add_parser("inspect")
    inspection.add_argument("--version-id", required=True)
    inspection.add_argument("--limit", type=int, default=10)
    inspection.set_defaults(handler=inspect_item)
    args = parser.parse_args()
    try:
        await args.handler(args)
    finally:
        await dispose_engine()


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    asyncio.run(main())
