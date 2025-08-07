from fastapi import APIRouter

from app.api.v1.endpoints import login, dashboard

api_router = APIRouter()

api_router.include_router(login.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(dashboard.router, prefix="/dashboard", tags=["Dashboard"])
