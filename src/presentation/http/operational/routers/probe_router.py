from typing import Annotated

from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse

from src.presentation.http.dependencies import provide_app_readiness

probe_router: APIRouter = APIRouter(tags=["probes"])


@probe_router.get(
    path="/livez",
    response_class=JSONResponse,
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_200_OK: {
            "description": "App is alive",
        },
    },
)
async def livez() -> JSONResponse:
    """Livez."""
    return JSONResponse(
        content={"status": "alive"},
        status_code=status.HTTP_200_OK,
    )


@probe_router.get(
    path="/readyz",
    response_class=JSONResponse,
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_200_OK: {
            "description": "App is ready to serve traffic",
        },
        status.HTTP_503_SERVICE_UNAVAILABLE: {
            "description": "App is not ready to serve traffic",
        },
    },
)
async def readyz(
    app_ready: Annotated[
        bool,
        Depends(dependency=provide_app_readiness),
    ],
) -> JSONResponse:
    """Readyz."""
    content: dict[str, str] = {"status": "ready"}
    status_code: int = status.HTTP_200_OK

    if not app_ready:
        content = {"status": "not_ready"}
        status_code = status.HTTP_503_SERVICE_UNAVAILABLE

    return JSONResponse(
        content=content,
        status_code=status_code,
    )
