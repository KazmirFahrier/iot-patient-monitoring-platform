from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "IoT Patient Monitoring Platform"
    database_url: str = "sqlite:///./data/iot_monitoring.db"
    alert_email_to: str = "care-team@example.com"
    gsm_recipient: str = "+8801000000000"
    smtp_host: str | None = None
    smtp_port: int = 587
    smtp_username: str | None = None
    smtp_password: str | None = None
    smtp_from: str = "alerts@example.com"
    bootstrap_demo_data: bool = True

    model_config = SettingsConfigDict(
        env_prefix="IOT_MONITORING_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )
