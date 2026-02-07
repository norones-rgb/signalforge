from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.logging import setup_logging
from app.routers.accounts import router as accounts_router
from app.routers.analytics import router as analytics_router
from app.routers.auth import router as auth_router
from app.routers.drafts import router as drafts_router
from app.routers.ideas import router as ideas_router
from app.routers.posts import router as posts_router
from app.routers.oauth import router as oauth_router
from app.routers.scheduler import router as scheduler_router
from app.routers.sources import router as sources_router
from app.routers.workspaces import router as workspaces_router


setup_logging()

app = FastAPI(title=settings.app_name)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(workspaces_router)
app.include_router(accounts_router)
app.include_router(sources_router)
app.include_router(ideas_router)
app.include_router(drafts_router)
app.include_router(scheduler_router)
app.include_router(posts_router)
app.include_router(analytics_router)
app.include_router(oauth_router)


@app.get("/health")
async def health() -> dict:
    return {"status": "ok"}
