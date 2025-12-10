from fastapi import FastAPI, Depends
from sqlmodel.ext.asyncio.session import AsyncSession
from app.database.database import create_db_and_tables, get_session
from app.database.models import User
from contextlib import asynccontextmanager
from scalar_fastapi import get_scalar_api_reference
from app.api.router import master_router

@asynccontextmanager
async def lifespan_handler(app: FastAPI):
    await create_db_and_tables()
    yield

app = FastAPI(
    lifespan=lifespan_handler,
)

app.include_router(master_router)

@app.get("/scalar", include_in_schema=False)
def get_scalar_docs():
    return get_scalar_api_reference(
        openapi_url=app.openapi_url,
        title="Scalar API",
    )
