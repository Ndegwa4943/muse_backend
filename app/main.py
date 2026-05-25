from fastapi import FastAPI
from app.core.config import settings

def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.PROJECT_NAME,
        version=settings.VERSION,
        openapi_url=f"{settings.API_V1_STR}/openapi.json"
    )

    # We will include our routers here in the next step
    # app.include_router(routes_journal.router, prefix=settings.API_V1_STR)

    @app.get("/")
    def root():
        return {"message": "Welcome to the Muse API. Contemplation awaits."}

    return app

app = create_app()