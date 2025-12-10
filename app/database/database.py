from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlmodel import SQLModel
import os
from dotenv import load_dotenv

load_dotenv()

# Make sure to use asyncpg driver for async PostgreSQL
DATABASE_URL = (
    f"postgresql+asyncpg://{os.getenv('POSTGRES_USER')}:{os.getenv('POSTGRES_PASSWORD')}"
    f"@{os.getenv('POSTGRES_HOST')}:{os.getenv('POSTGRES_PORT')}/{os.getenv('POSTGRES_DB')}"
)
engine = create_async_engine(
    # database type/dialect and file name
    url=DATABASE_URL,
    # Log sql queries
    # echo=True,
)

async def create_db_and_tables():
    async with engine.begin() as conn:
        # Import models here to ensure they're registered with SQLModel.metadata
        from .models import User  # noqa: F401
        await conn.run_sync(SQLModel.metadata.create_all)

# Dependency for FastAPI
async def get_session():
    async_session = sessionmaker(
        bind=engine, class_=AsyncSession, expire_on_commit=False,
    )

    async with async_session() as session:
        yield session