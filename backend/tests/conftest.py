import os
import subprocess
from pathlib import Path

# Must run before any app module is imported: point the app at the TEST database.
_dev_url = os.environ["DATABASE_URL"]
TEST_DATABASE_URL = _dev_url.rsplit("/", 1)[0] + "/rag_test"
assert TEST_DATABASE_URL != _dev_url, "Refusing to run tests against the dev database"
os.environ["DATABASE_URL"] = TEST_DATABASE_URL

import httpx  # noqa: E402
import pytest  # noqa: E402
import pytest_asyncio  # noqa: E402
from sqlalchemy import text  # noqa: E402

from app.api.deps import get_embedding_service, get_llm_service  # noqa: E402
from app.api.ratelimit import ALL_LIMITERS  # noqa: E402
from app.db.engine import engine  # noqa: E402
from app.main import app  # noqa: E402
from tests.fakes import FakeEmbeddingService, FakeLLMService  # noqa: E402


@pytest.fixture(scope="session")
def migrated_database() -> None:
    backend_dir = Path(__file__).resolve().parent.parent
    subprocess.run(["alembic", "upgrade", "head"], cwd=backend_dir, check=True)


@pytest_asyncio.fixture(scope="session", autouse=True)
async def _dispose_engine():
    yield
    await engine.dispose()


@pytest_asyncio.fixture(autouse=True)
async def clean_tables(migrated_database):
    async with engine.begin() as connection:
        await connection.execute(
            text("TRUNCATE TABLE chunks, documents, users RESTART IDENTITY CASCADE")
        )
    yield


@pytest.fixture(autouse=True)
def relaxed_rate_limits():
    """Normal tests must not be throttled. Rate-limit tests lower the limits themselves."""
    saved = [(limiter, limiter.limit, limiter.window) for limiter in ALL_LIMITERS]
    for limiter in ALL_LIMITERS:
        limiter.reset()
        limiter.limit = 10**9
    yield
    for limiter, limit, window in saved:
        limiter.limit, limiter.window = limit, window
        limiter.reset()


@pytest.fixture
def fake_llm() -> FakeLLMService:
    return FakeLLMService()


@pytest_asyncio.fixture
async def client(fake_llm):
    app.dependency_overrides[get_embedding_service] = lambda: FakeEmbeddingService()
    app.dependency_overrides[get_llm_service] = lambda: fake_llm
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as http_client:
        yield http_client
    app.dependency_overrides.clear()