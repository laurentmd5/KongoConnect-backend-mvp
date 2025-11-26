from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from app.core.config import settings
from app.api.v1.api import api_router
from app.db.session import engine
from app.models.base_class import Base
from app.core.cache import CacheManager
from app.core.scheduler import scheduler_service
import logging
logging.basicConfig(level=logging.DEBUG)

async def create_tables():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await create_tables()

    try:
        redis = CacheManager.get_client()
        await redis.ping()
        print("Redis Connected")
    except Exception as e:
        print(f"Redis not available: {e}")

    # Start Scheduler
    scheduler_service.start()
    print("APScheduler started (Auto-Release active)")

    yield

    # Shutdown
    scheduler_service.stop()
    await CacheManager.close()
    print("System stopped")

app = FastAPI(
    title=settings.PROJECT_NAME,
    version="MVP-1.0-Cafard",
    description="Backend KoCo - Services + Escrow + AutoRelease",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix=settings.API_V1_STR)

@app.get("/")
def root():
    return {"status": "KoCo Backend Ready", "scheduler": "active"}
