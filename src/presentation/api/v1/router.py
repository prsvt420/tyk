from fastapi import APIRouter

from src.presentation.api.v1.controllers import router as short_links_router

router: APIRouter = APIRouter()

router.include_router(short_links_router, tags=["short-links"])
