from fastapi import APIRouter, status
from fastapi.responses import JSONResponse

probe_router: APIRouter = APIRouter(tags=["probes"])


@probe_router.get(
    path="/livez",
    response_class=JSONResponse,
    status_code=status.HTTP_200_OK,
)
async def livez() -> JSONResponse:
    """Livez."""
    return JSONResponse(
        content={"status": "alive"},
        status_code=status.HTTP_200_OK,
    )
