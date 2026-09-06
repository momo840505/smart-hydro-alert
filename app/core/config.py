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

    # Replaces the previous jwt_secret / jwt_algorithm / jwt_expire_minutes
    # settings, which were defined but never actually checked anywhere in
    # the app (every route was reachable with no credentials at all). A
    # single shared admin API key is a better fit for this project: there
    # is no user login flow or multiple accounts, just one operator's
    # dashboard talking to one backend. See app/core/security.py.
    admin_api_key: str = ""

    # Comma-separated list of origins allowed to call this API with
    # credentials. Never combine "*" here with allow_credentials=True in
    # app/main.py -- see that file's comment for why.
    cors_allowed_origins: str = "http://localhost:5173,http://localhost:3000"

    telegram_bot_token: str = ""
    telegram_chat_id: str = ""

    alert_duration_threshold_sec: int = 300
    timestamp_skew_past_sec: int = 3600
    timestamp_skew_future_sec: int = 300
    mqtt_max_payload_bytes: int = 512

    @property
    def cors_allowed_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_allowed_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
