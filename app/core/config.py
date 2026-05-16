from pydantic_settings import BaseSettings
from pathlib import Path

# get root directory
ROOT_DIR = Path(__file__).parent.parent.parent

class Settings(BaseSettings):
    DATABASE_URL: str
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    REDIS_URL: str
    MAIL_USERNAME: str
    MAIL_PASSWORD: str
    MAIL_FROM: str
    MAIL_SERVER: str = "smtp.gmail.com"
    MAIL_PORT: int = 587

    RABBITMQ_URL: str = "amqp://guest:guest@localhost/"

    STRIPE_SECRET_KEY: str
    model_config = {
        "env_file": str(ROOT_DIR / ".env"),
        "env_file_encoding": "utf-8"
    }

settings = Settings()