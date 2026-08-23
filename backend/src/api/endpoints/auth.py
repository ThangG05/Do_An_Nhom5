from fastapi import APIRouter

router = APIRouter(prefix="/auth", tags=["Auth"])

@router.get("/health")
async def health():
    return {"module": "auth"}
