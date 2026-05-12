# src/ais_recorder/config.py from https://github.com/sgofferj/python-ais-recorder
#
# Copyright Stefan Gofferje
#
# Licensed under the Gnu General Public License Version 3 or higher (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at https://www.gnu.org/licenses/gpl-3.0.en.html

"""Configuration management for the AIS Recorder."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    mariadb_host: str = "localhost"
    mariadb_port: int = 3306
    mariadb_user: str
    mariadb_password: str
    mariadb_database: str = "ais_recorder"

    api_workers: int = 1
    retention_hours: int = 48

    digitraffic_user: str = "python-ais-recorder/1.0"
    digitraffic_mqtt_url: str = "meri.digitraffic.fi"
    digitraffic_mqtt_port: int = 443

    log_level: str = "INFO"

    @property
    def mariadb_url(self) -> str:
        """Return the async MariaDB connection URL."""
        return (
            f"mysql+aiomysql://{self.mariadb_user}:{self.mariadb_password}"
            f"@{self.mariadb_host}:{self.mariadb_port}/{self.mariadb_database}"
        )

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )


settings = Settings()
