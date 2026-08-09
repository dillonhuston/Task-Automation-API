from pydantic_settings import BaseSettings
from pydantic import Field, SecretStr
from typing import Optional

class Settings(BaseSettings):
    
    DATABASE_URL: str = Field(env="DATABASE_URL")

    JWT_SECRET: SecretStr = Field(env="JWT_SECRET")
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRATION_MINUTES: int = 60

    MASTER_KEY: SecretStr = Field(env="MASTER_KEY")

    BASE_DIR: str = "."

    LOG_LEVEL: str = "INFO"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"  

settings = Settings()