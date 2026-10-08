"""FastAPI application entry point."""
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app import models  # noqa: F401  (registers tables on Base.metadata)
from app.config import LOG_LEVEL
from app.database import Base, engine
from app.routers import addresses

logging.basicConfig(level=LOG_LEVEL, format="%(asctime)s %(levelname)s [%(name)s] %(message)s")
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(_: FastAPI):
    Base.metadata.create_all(bind=engine)
    logger.info("Database ready")
    yield


app = FastAPI(title="Address Book API", version="1.0.0", lifespan=lifespan)
app.include_router(addresses.router)
