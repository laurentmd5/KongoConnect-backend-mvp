from pydantic_settings import BaseSettings
from pydantic import computed_field

class Settings(BaseSettings):
    PROJECT_NAME: str = "KoCo API"
    API_V1_STR: str = "/api/v1"
    SECRET_KEY: str = "DEV_SECRET"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7 

    # Environnement
    ENVIRONMENT: str = "development"  # "development" ou "production"

    # Database - PostgreSQL (optionnel en dev)
    POSTGRES_USER: str = "koco_user"
    POSTGRES_PASSWORD: str = "koco_pass"
    POSTGRES_SERVER: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_DB: str = "koco_db"

    # Cache
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379

    @computed_field
    @property
    def SQLALCHEMY_DATABASE_URI(self) -> str:
        """
        Retourne l'URI de la base de données selon l'environnement:
        - Dev: SQLite (aiosqlite)
        - Prod: PostgreSQL (asyncpg)
        """
        if self.ENVIRONMENT == "production":
            # Production: PostgreSQL
            return f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_SERVER}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        else:
            # Development: SQLite (fichier local)
            return "sqlite+aiosqlite:///./koco.db"

    @computed_field
    @property
    def REDIS_URL(self) -> str:
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/0"

    class Config:
        env_file = ".env"

settings = Settings()