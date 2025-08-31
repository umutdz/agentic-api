from typing import Literal, Optional

from pydantic import ConfigDict
from pydantic_settings import BaseSettings


class Config(BaseSettings):
    # API Settings
    APP_ENV: str
    APP_DEBUG: bool
    APP_STR: str = "/api/v1"
    APP_NAME: str = "{name} API"
    APP_VERSION: str = "v1"

    # POSTGRES
    POSTGRES_PASSWORD: str
    POSTGRES_HOST: str
    POSTGRES_DB: str
    POSTGRES_USER: str
    POSTGRES_PORT: int

    # RabbitMQ
    RABBITMQ_DEFAULT_PASS: str
    RABBITMQ_DEFAULT_USER: str
    RABBITMQ_HOST: str
    RABBITMQ_PORT: int

    SESSION_TTL_SECOND: int = 30 * 24 * 60 * 60

    # origins
    STAGING_ORIGIN: list = []
    PRODUCTION_ORIGIN: list = []

    # QUEUE NAME
    QUEUE_NAME: str

    # Rate Limiter Settings
    RATE_LIMIT_TIMES: int = 100  # Number of requests allowed
    RATE_LIMIT_SECONDS: int = 60  # Time window in seconds

    # JWT Settings
    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    JWT_REFRESH_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 30  # 30 days

    # Redis
    REDIS_URL: str
    REDIS_PREFIX: str = "agentic_ai:"

    # API Key
    API_KEY: str

    # MongoDB
    MONGO_HOST: str
    MONGO_PORT: int
    MONGO_USER: str
    MONGO_PASSWORD: str
    MONGO_DB: str

    # LLM Settings
    LLM_PROVIDER: str
    LLM_MODEL_CONTENT: str
    LLM_MODEL_CODE: str
    LLM_TIMEOUT_S: int
    LLM_MAX_RETRIES: int
    OPENAI_API_KEY: str
    OPENAI_BASE_URL: str

    # Web / ContentAgent
    WEB_USER_AGENT: str = "AgenticAPI/ContentAgent"
    WEB_TIMEOUT_S: int = 10
    WEB_WHITELIST: str = ""  # "wikipedia.org, mdn.mozilla.org" gibi
    WEB_SEARCH_PROVIDER: Optional[Literal["ddg", "serpapi", "bing"]] = None
    SERPAPI_API_KEY: Optional[str] = None
    SERPAPI_ENGINE: Optional[str] = "duckduckgo"

    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FILE: str = "logs/app.log"

    @property
    def ORIGIN(self):
        if self.APP_ENV == "PRODUCTION":
            return self.PRODUCTION_ORIGIN
        else:
            return self.STAGING_ORIGIN

    model_config = ConfigDict(env_file=".env", case_sensitive=True, extra="allow")


config = Config()
