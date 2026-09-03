from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase

# Asynchronous SQLite URL (for local development)
DATABASE_URL = "sqlite+aiosqlite:///./campus_api.db"

# Create async engine
engine = create_async_engine(DATABASE_URL, echo=True)

# Create session factory
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False
)

# Base class for ORM models
class Base(DeclarativeBase):
    pass

# Dependency to yield database sessions in FastAPI routes
async def get_db():
    async with AsyncSessionLocal() as session:
        yield session