from fastapi import APIRouter

from src.presentation.http.api.v1.routers import short_link_router

api_v1_router: APIRouter = APIRouter()

api_v1_router.include_router(router=short_link_router)
