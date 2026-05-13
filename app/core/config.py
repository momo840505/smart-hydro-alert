from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "smart-water-monitor"
    app_env: str = "development"
    app_host: str = "0.0.0.0"
    app_port: int = 8000
    log_level: str = "INFO"

    mongo_uri: str = "mongodb://localhost:27017"
    mongo_db: str = "smart_water"

    mqtt_host: str = "localhost"
    mqtt_port: int = 1883
    mqtt_username: str = ""
    mqtt_password: str = ""
    mqtt_client_id: str = "fastapi-backend"
    mqtt_topic_sensor: str = "home/+/+/sensor"
    mqtt_topic_alert: str = "home/+/+/alert"
    mqtt_topic_status: str = "home/+/+/status"

    jwt_secret: str = "change-me-to-a-long-random-string"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 60

    telegram_bot_token: str = ""
    telegram_chat_id: str = ""

    alert_duration_threshold_sec: int = 300
    timestamp_skew_past_sec: int = 3600
    timestamp_skew_future_sec: int = 300
    mqtt_max_payload_bytes: int = 512


@lru_cache
def get_settings() -> Settings:
    return Settings()
