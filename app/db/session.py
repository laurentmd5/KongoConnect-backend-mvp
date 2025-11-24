from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from app.core.config import settings

# 1. Détection automatique : Est-ce qu'on est sur SQLite ?
is_sqlite = "sqlite" in settings.SQLALCHEMY_DATABASE_URI

# 2. Configuration des arguments de connexion
connect_args = {}
if is_sqlite:
    # INDISPENSABLE pour éviter les erreurs de thread avec SQLite + FastAPI
    connect_args = {"check_same_thread": False}

# 3. Création de l'engine
engine = create_async_engine(
    settings.SQLALCHEMY_DATABASE_URI,
    future=True,
    echo=True, # Mettez True en dev pour voir les requêtes SQL dans la console
    connect_args=connect_args # Injecte la config spéciale si c'est SQLite
)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)

async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()