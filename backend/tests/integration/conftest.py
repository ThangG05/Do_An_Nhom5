import uuid

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from src.api.routes import router
from src.core.security import create_access_token, hash_password
from src.db.models.user import AccountStatus, Profile, SystemRole, User
from src.db.session import engine, get_db


@pytest.fixture
def db_session() -> Session:
    connection = engine.connect()
    transaction = connection.begin()
    session = Session(bind=connection, join_transaction_mode="create_savepoint")
    try:
        yield session
    finally:
        session.close()
        transaction.rollback()
        connection.close()


@pytest.fixture
def app(db_session: Session, monkeypatch: pytest.MonkeyPatch) -> FastAPI:
    application = FastAPI()
    application.include_router(router, prefix="/api/v1")

    def override_db():
        yield db_session

    application.dependency_overrides[get_db] = override_db
    monkeypatch.setattr("src.services.post_service.create_download_url", lambda media: f"https://r2.test/{media.object_key}")
    monkeypatch.setattr("src.services.user_service.create_download_url", lambda media: f"https://r2.test/{media.object_key}")
    return application


@pytest.fixture
def client(app: FastAPI):
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def make_user(db_session: Session):
    def factory(*, role: SystemRole = SystemRole.USER, name: str = "Integration User", password: str | None = None) -> User:
        suffix = uuid.uuid4().hex[:12]
        user = User(
            email=f"integration-{suffix}@hvnh.edu.vn",
            username=f"it_{suffix}",
            password_hash=hash_password(password) if password else "!integration-only",
            status=AccountStatus.ACTIVE,
            system_role=role,
        )
        db_session.add(user)
        db_session.flush()
        db_session.add(Profile(user_id=user.id, full_name=name, student_code=f"IT{suffix[:8]}", social_links={}))
        db_session.commit()
        db_session.refresh(user)
        return user

    return factory


@pytest.fixture
def auth_headers():
    def factory(user: User) -> dict[str, str]:
        token, _ = create_access_token(str(user.id))
        return {"Authorization": f"Bearer {token}"}

    return factory


@pytest.fixture
def active_group(db_session: Session):
    row = db_session.execute(
        __import__("sqlalchemy").text("SELECT id,name FROM groups WHERE status='ACTIVE' ORDER BY name LIMIT 1")
    ).mappings().first()
    if row is None:
        pytest.skip("Database tích hợp chưa có nhóm ACTIVE.")
    return row
