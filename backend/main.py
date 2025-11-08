from datetime import datetime, timezone
from typing import Dict

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from core.config import get_settings
from routers import ad_accounts, ad_spend, channels, projects, reconciliations, reports, topups

settings = get_settings()

app = FastAPI(title=settings.app_name, debug=settings.debug)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(projects.router)
app.include_router(channels.router)
app.include_router(ad_accounts.router)
app.include_router(ad_spend.router)
app.include_router(reconciliations.router)
app.include_router(reports.router)
app.include_router(topups.router)


@app.get("/healthz")
async def healthz() -> Dict[str, str]:
    """Return service health status."""
    return {
        "status": "ok",
        "timestamp": datetime.now(tz=timezone.utc).isoformat(),
    }



