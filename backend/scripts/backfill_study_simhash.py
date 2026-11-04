"""Backfill SimHash fingerprints for active study-library files.

Run from backend after applying migrations and configuring DB/R2/Modal:
    python -m scripts.backfill_study_simhash
Use --rebuild once when changing the text/OCR extraction pipeline.
"""

from __future__ import annotations

import argparse
import asyncio

from sqlalchemy import text

from src.config import settings
from src.db.session import SessionLocal
from src.services.storage_service import get_r2_client
from src.services.study_document_dedup import (
    SIMHASH_VERSION,
    compute_simhash64,
    extract_document_text_for_fingerprint,
    simhash_bands,
)


async def run(rebuild: bool) -> None:
    if not settings.R2_STUDY_BUCKET_NAME:
        raise RuntimeError("R2_STUDY_BUCKET_NAME is required")
    db = SessionLocal()
    scanned = indexed = skipped = 0
    try:
        condition = "TRUE" if rebuild else "f.simhash64 IS NULL"
        files = db.execute(text(f"""
            SELECT f.id, f.r2_object_key, f.extension, f.checksum_sha256, d.group_id
            FROM study_document_files f
            JOIN study_documents d ON d.id=f.document_id
            WHERE {condition} AND f.deleted_at IS NULL
              AND d.deleted_at IS NULL AND d.status IN ('PENDING','APPROVED')
            ORDER BY d.created_at, f.id
        """)).mappings().all()
        client = get_r2_client()
        ocr_provider = None
        for row in files:
            scanned += 1
            try:
                result = client.get_object(Bucket=settings.R2_STUDY_BUCKET_NAME, Key=row["r2_object_key"])
                body = result["Body"]
                try:
                    data = body.read()
                finally:
                    body.close()
                extracted, status, ocr_provider = await extract_document_text_for_fingerprint(
                    data, row["extension"], ocr_provider
                )
                signature = compute_simhash64(extracted) if status in {"SCANNED", "OCR_SCANNED"} else None
                if status == "OCR_UNAVAILABLE":
                    skipped += 1
                    db.rollback()
                    continue
                db.execute(text("DELETE FROM study_document_file_simhash_bands WHERE file_id=:id"),
                           {"id": row["id"]})
                db.execute(text("UPDATE study_document_files SET simhash64=:signature WHERE id=:id"),
                           {"signature": signature, "id": row["id"]})
                if signature:
                    db.execute(text("""
                        INSERT INTO study_document_file_simhash_bands(file_id,group_id,band_index,band_value)
                        VALUES(:file_id,:group_id,:band_index,:band_value)
                        ON CONFLICT(file_id,band_index) DO UPDATE SET band_value=EXCLUDED.band_value
                    """), [{"file_id": row["id"], "group_id": row["group_id"],
                           "band_index": index, "band_value": value}
                          for index, value in simhash_bands(signature)])
                db.execute(text("""
                    INSERT INTO study_document_scan_fingerprint_cache(
                        checksum_sha256,extension,algorithm_version,simhash64,scan_status,updated_at
                    ) VALUES(:sha256,:extension,:version,:signature,:status,now())
                    ON CONFLICT(checksum_sha256,extension,algorithm_version) DO UPDATE SET
                        simhash64=EXCLUDED.simhash64,scan_status=EXCLUDED.scan_status,updated_at=now()
                """), {"sha256": row["checksum_sha256"], "extension": row["extension"],
                       "version": SIMHASH_VERSION, "signature": signature,
                       "status": "NO_TEXT" if status in {"SCANNED", "OCR_SCANNED"} and not signature else status})
                db.commit()
                indexed += 1
            except Exception:
                db.rollback()
                skipped += 1
        print(f"SimHash backfill complete: scanned={scanned}, indexed={indexed}, skipped={skipped}")
    finally:
        db.close()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--rebuild", action="store_true", help="Re-extract and refresh all active file fingerprints")
    args = parser.parse_args()
    asyncio.run(run(args.rebuild))


if __name__ == "__main__":
    main()
