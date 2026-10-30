"""Конфигурация серверного приложения через переменные окружения."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Глобальные настройки веб-сервиса учёта дедлайнов учебной группы."""

    PROJECT_NAME: str = "Веб-сервис для учёта заданий и дедлайнов учебной группы"
    APP_ENV: str = "development"
    DEBUG: bool = True
    API_V1_PREFIX: str = "/api/v1"

    # PostgreSQL 15+
    POSTGRES_USER: str = "deadline_user"
    POSTGRES_PASSWORD: str = "deadline_secret_password"
    POSTGRES_DB: str = "deadline_tracker_db"
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432
    DATABASE_URL: str = (
        "postgresql+psycopg2://deadline_user:deadline_secret_password@localhost:5432/deadline_tracker_db"
    )

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"
    # Хранилище счётчиков входа и CAPTCHA: "auto" (Redis, при недоступности — память), "redis", "memory"
    KV_BACKEND: str = "auto"

    # JWT и ступенчатая защита от брутфорса (п. 4.2.1, 4.2.2 ТЗ)
    JWT_SECRET_KEY: str = "change_this_super_secret_jwt_key_in_production_min_32_chars"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    BCRYPT_ROUNDS: int = 12
    BRUTEFORCE_WINDOW_SECONDS: int = 900
    BRUTEFORCE_CAPTCHA_THRESHOLD: int = 5
    BRUTEFORCE_LOCKOUT_THRESHOLD: int = 10
    BRUTEFORCE_LOCKOUT_DURATION_SECONDS: int = 900
    BRUTEFORCE_IP_THRESHOLD: int = 20
    CAPTCHA_TTL_SECONDS: int = 300

    # Инвайт-коды учебных групп (п. 4.2.1.1 ТЗ)
    INVITE_CODE_TTL_DAYS: int = 30

    # Хранилище файлов S3 / MinIO и политика проверки архивов (п. 4.11.3, 4.11.5 ТЗ)
    S3_ENDPOINT_URL: str = "http://localhost:9000"
    S3_ACCESS_KEY: str = "minioadmin"
    S3_SECRET_KEY: str = "minioadmin_secret"
    S3_BUCKET_NAME: str = "study-materials-and-reports"
    MAX_UPLOAD_SIZE_MB: int = 50
    MAX_ARCHIVE_UNPACKED_SIZE_MB: int = 200
    MAX_ARCHIVE_NESTING_LEVEL: int = 2

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


settings = Settings()
