from contextlib import asynccontextmanager
from collections.abc import AsyncIterator

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from src.api.routes import router
from src.agents.rag_runtime import rag_lifespan
from src.config import settings
from src.services.realtime_service import manager


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    await manager.start()
    try:
        async with rag_lifespan():
            yield
    finally:
        await manager.stop()


app = FastAPI(title="HVNH Hub API", version="1.0.0", lifespan=lifespan)

@app.middleware("http")
async def maintenance_guard(request:Request,call_next):
    allowed=("/api/v1/auth/","/api/v1/system/status","/docs","/openapi.json","/redoc")
    if request.url.path.startswith(allowed):return await call_next(request)
    from src.db.session import SessionLocal
    from src.services.system_service import maintenance
    from src.core.security import decode_access_token
    from src.db.models.user import User,SystemRole
    with SessionLocal() as db:
        state=maintenance(db)
        if state.enabled:
            bypass=False;header=request.headers.get("authorization","")
            if header.startswith("Bearer "):
                try:
                    user=db.get(User,__import__('uuid').UUID(decode_access_token(header[7:])))
                    bypass=bool(user and user.system_role==SystemRole.SUPER_ADMIN)
                except Exception:pass
            if not bypass:return JSONResponse(status_code=503,content={"detail":state.message,"maintenance":True,"expected_end_at":state.expected_end_at.isoformat() if state.expected_end_at else None})
    return await call_next(request)

@app.middleware("http")
async def rate_limit_guard(request:Request,call_next):
    if request.method in {"POST","PUT","PATCH"}:
        path=request.url.path;bucket=None
        if path.endswith("/auth/login"):bucket="login"
        elif path.endswith("/register/request-code"):bucket="otp"
        elif "/auth/password/" in path:bucket="reset"
        elif path.endswith("/reports"):bucket="report"
        elif "/media/upload/" in path or path.endswith("/media/presign"):bucket="upload"
        elif "/posts" in path or "/comments" in path or "/messages" in path:bucket="content"
        if bucket:
            from src.db.session import SessionLocal
            from src.services.rate_limit_service import consume
            # Forwarding headers are ignored until a trusted proxy is configured;
            # otherwise a caller could spoof them to bypass the IP limit.
            identifier=request.client.host if request.client else "unknown"
            auth=request.headers.get("authorization","")
            if auth.startswith("Bearer "):
                try:
                    from src.core.security import decode_access_token
                    identifier=f"user:{decode_access_token(auth[7:])}"
                except Exception:pass
            with SessionLocal() as db:allowed,retry=consume(db,identifier,bucket)
            if not allowed:return JSONResponse(status_code=429,content={"detail":"Bạn thao tác quá nhanh. Vui lòng thử lại sau."},headers={"Retry-After":str(retry)})
    return await call_next(request)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router, prefix="/api/v1")
