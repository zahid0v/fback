from fastapi import APIRouter
from .routers import user, openpack

master_router = APIRouter()

master_router.include_router(user.router)
master_router.include_router(openpack.router)