from fastapi import APIRouter

from src.presentation.api.redirect.controllers.redirect_controller import (
    router as redirect_router,
)

router: APIRouter = APIRouter()

router.include_router(redirect_router, tags=["redirect"])
