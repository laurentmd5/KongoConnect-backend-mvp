from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from app.core.config import settings
from app.api.v1.api import api_router
from app.db.session import engine
from app.models.base_class import Base
from app.core.cache import CacheManager

async def create_tables():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Démarrage
    await create_tables()
    try:
        redis = CacheManager.get_client()
        await redis.ping()
        print("✅ Redis Connecté")
    except Exception as e:
        print(f"❌ Erreur Redis: {e}")
    
    yield
    
    # Arrêt
    await CacheManager.close()

app = FastAPI(
    title=settings.PROJECT_NAME,
    version="2.0.0",
    description="KoCo API - Brazzaville",
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
    return {"status": "KoCo Backend Online 🇨🇬"}