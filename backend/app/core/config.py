from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    # API Settings
    PROJECT_NAME: str = "Real-Time Urban Intelligence & Decision System"
    API_V1_STR: str = "/api/v1"

    # PostgreSQL Setup
    POSTGRES_USER: str = "rtuids_user"
    POSTGRES_PASSWORD: str = "rtuids_password"
    POSTGRES_SERVER: str = "localhost"
    POSTGRES_PORT: str = "5432"
    POSTGRES_DB: str = "rtuids_db"

    @property
    def DATABASE_URL(self) -> str:
        return f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_SERVER}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"

    # Redis Setup
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    
    @property
    def REDIS_URL(self) -> str:
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"

    # Kafka/Stream limits
    STREAM_NAME: str = "sensor_events"
    MAX_BATCH_SIZE: int = 100
    
    model_config = SettingsConfigDict(case_sensitive=True, env_file=".env")

settings = Settings()
