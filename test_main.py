import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.pool import StaticPool

from database import Base, get_db
from main import app

# Setup isolated in-memory SQLite database for testing
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

test_engine = create_async_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

TestingSessionLocal = async_sessionmaker(
    bind=test_engine, class_=AsyncSession, expire_on_commit=False
)


# Override database dependency
async def override_get_db():
    async with TestingSessionLocal() as session:
        yield session


app.dependency_overrides[get_db] = override_get_db

API_HEADERS = {"X-API-Key": "supersecretkey123", "x-user-id": "user_1"}


@pytest.fixture(autouse=True, scope="function")
async def setup_database():
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.mark.asyncio
async def test_create_and_read_item():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        # Happy Path: Create Item
        payload = {
            "title": "Test Wallet",
            "description": "Black leather wallet",
            "category": "Accessories",
            "location": "Library",
            "status": "lost",
        }
        res = await ac.post("/items", json=payload, headers=API_HEADERS)
        assert res.status_code == 201
        data = res.json()
        assert data["title"] == "Test Wallet"
        assert data["owner_id"] == "user_1"

        # Read Item
        item_id = data["id"]
        res_get = await ac.get(f"/items/{item_id}")
        assert res_get.status_code == 200
        assert res_get.json()["id"] == item_id


@pytest.mark.asyncio
async def test_validation_failure():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        # Invalid status value
        payload = {
            "title": "Bad Item",
            "category": "General",
            "location": "Cafeteria",
            "status": "invalid_status",
        }
        res = await ac.post("/items", json=payload, headers=API_HEADERS)
        assert res.status_code == 400


@pytest.mark.asyncio
async def test_authorization_boundary():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        # Create item as user_1
        payload = {
            "title": "Keys",
            "category": "Keys",
            "location": "Gym",
            "status": "found",
        }
        res = await ac.post("/items", json=payload, headers=API_HEADERS)
        item_id = res.json()["id"]

        # Attempt deletion as user_2 (Unauthorized boundary)
        unauth_headers = {"X-API-Key": "supersecretkey123", "x-user-id": "user_2"}
        res_del = await ac.delete(f"/items/{item_id}", headers=unauth_headers)
        assert res_del.status_code == 403


@pytest.mark.asyncio
async def test_missing_api_key():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        payload = {
            "title": "Phone",
            "category": "Electronics",
            "location": "Lab",
            "status": "lost",
        }
        res = await ac.post("/items", json=payload)
        assert res.status_code == 401