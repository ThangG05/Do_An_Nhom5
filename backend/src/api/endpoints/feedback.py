from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from src.api.dependencies import CurrentUser
from src.db.session import get_db
from src.services.email_service import EmailDeliveryError, send_user_feedback
from src.services.rate_limit_service import consume

router = APIRouter(prefix="/feedback", tags=["Feedback"])
Db = Annotated[Session, Depends(get_db)]


class FeedbackRequest(BaseModel):
    message: str = Field(min_length=10, max_length=4000)


@router.post("", status_code=200)
def submit_feedback(payload: FeedbackRequest, user: CurrentUser, db: Db):
    message = payload.message.strip()
    if len(message) < 10:
        raise HTTPException(status_code=422, detail="Nội dung góp ý cần ít nhất 10 ký tự.")
    allowed, retry_after = consume(db, str(user.id), "report")
    if not allowed:
        raise HTTPException(status_code=429, detail=f"Bạn gửi quá nhiều góp ý. Thử lại sau {retry_after} giây.")
    try:
        send_user_feedback(
            sender_email=user.email,
            sender_name=user.profile.full_name if user.profile else user.username,
            message=message,
        )
    except EmailDeliveryError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    return {"message": "Đã gửi góp ý tới Ban quản trị."}
