import logging
import threading
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import auth
from export.chat.agent import get_export_agent
from export.routes import router as export_router
from mkt.chat.agent import get_mkt_agent
from mkt.routes import router as mkt_router

logger = logging.getLogger("uvicorn.error")


def _warm(name, build):
    # Building an agent queries the view's brand codes (~18s for mkt), so do it
    # at boot instead of on the first user's question. Failure is non-fatal:
    # the agent is retried lazily on the next request.
    try:
        build()
        logger.info("%s agent warmed", name)
    except Exception:
        logger.exception("%s agent warm-up failed; will retry on first request", name)


@asynccontextmanager
async def lifespan(app: FastAPI):
    for name, build in (("export", get_export_agent), ("mkt", get_mkt_agent)):
        threading.Thread(target=_warm, args=(name, build), daemon=True).start()
    yield


app = FastAPI(title="Assistant API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(export_router)
app.include_router(mkt_router)
app.include_router(auth.router)

@app.get("/")
def read_root():
    return {"message": "API Server is running!"}
