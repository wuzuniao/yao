import os
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str
    PROJECT_NAME: str = "My Project"
    API_V1_STR: str = "/api/v1"

    class Config:
        @staticmethod
        def get_env_file():
            if os.getenv("ENV") == "prod":
                return ".env.prod"
            return ".env.dev"

        env_file = get_env_file.__func__()
        extra = "allow"


settings = Settings()
