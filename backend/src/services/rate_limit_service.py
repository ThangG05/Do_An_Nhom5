from datetime import UTC, datetime

from sqlalchemy import text
from sqlalchemy.orm import Session

from src.config import settings


def _limits() -> dict[str, int]:
    return {
        "login": settings.RATE_LIMIT_LOGIN,
        "otp": settings.RATE_LIMIT_OTP,
        "reset": settings.RATE_LIMIT_RESET,
        "report": settings.RATE_LIMIT_REPORT,
        "upload": settings.RATE_LIMIT_UPLOAD,
        "content": settings.RATE_LIMIT_CONTENT,
    }


def consume(db: Session, identifier: str, bucket: str) -> tuple[bool, int]:
    limit = _limits().get(bucket)
    if limit is None:
        raise ValueError(f"Unknown rate-limit bucket: {bucket}")

    window = settings.RATE_LIMIT_WINDOW_SECONDS
    row = db.execute(
        text(
            """
            INSERT INTO request_rate_limits (
                identifier, bucket, window_start, request_count
            )
            VALUES (
                :identifier,
                :bucket,
                to_timestamp(floor(extract(epoch from now()) / :window) * :window),
                1
            )
            ON CONFLICT (identifier, bucket, window_start)
            DO UPDATE SET request_count = request_rate_limits.request_count + 1
            RETURNING request_count, window_start
            """
        ),
        {"identifier": identifier[:255], "bucket": bucket, "window": window},
    ).first()
    db.commit()

    remaining = max(
        1,
        window - int((datetime.now(UTC) - row.window_start).total_seconds()),
    )
    return row.request_count <= limit, remaining
