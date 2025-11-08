import os
import sys
import uuid
from pathlib import Path
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import event
from sqlalchemy.dialects.postgresql import JSONB, UUID as PG_UUID
from sqlalchemy.ext.compiler import compiles

# 把项目根目录加入 Python 搜索路径
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

TEST_DB_PATH = Path("test.db")
if TEST_DB_PATH.exists():
    TEST_DB_PATH.unlink()

os.environ.setdefault("DATABASE_URL", f"sqlite:///./{TEST_DB_PATH.name}")
os.environ.setdefault("JWT_SECRET", "test-secret")
os.environ.setdefault("ALLOWED_ORIGINS", "http://localhost:3000")

from backend.core.db import Base, get_engine, get_session_factory  # noqa: E402
from backend.core.security import AuthenticatedUser, get_current_user  # noqa: E402
from backend.main import app  # noqa: E402


@compiles(PG_UUID, "sqlite")
def compile_uuid_sqlite(*_args, **_kwargs):
    return "CHAR(36)"


@compiles(JSONB, "sqlite")
def compile_jsonb_sqlite(*_args, **_kwargs):
    return "TEXT"


@pytest.fixture(scope="session")
def engine():
    engine = get_engine()

    @event.listens_for(engine, "connect")
    def register_uuid_function(dbapi_connection, _):
        dbapi_connection.create_function("gen_random_uuid", 0, lambda: str(uuid.uuid4()))

    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)
    if TEST_DB_PATH.exists():
        TEST_DB_PATH.unlink()


@pytest.fixture(autouse=True)
def reset_database(engine):
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield


@pytest.fixture(scope="session")
def test_user():
    return AuthenticatedUser(
        id=str(uuid4()),
        role="admin",
        email="tester@example.com",
        raw_claims={"source": "pytest"},
    )


@pytest.fixture(scope="session")
def client(engine, test_user):
    app.dependency_overrides[get_current_user] = lambda: test_user
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.pop(get_current_user, None)


@pytest.fixture
def db_session(engine):
    session_factory = get_session_factory()
    session = session_factory()
    try:
        yield session
    finally:
        session.close()
