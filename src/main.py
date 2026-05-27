from fastapi import FastAPI


def create_app() -> FastAPI:
    """Create and configure FastAPI application."""
    app: FastAPI = FastAPI(
        title="Тык",
        version="0.1.0",
        description="Сокращатель URL-адресов",
    )
    return app


app: FastAPI = create_app()
