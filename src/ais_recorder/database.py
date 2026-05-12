# src/ais_recorder/database.py from https://github.com/sgofferj/python-ais-recorder
#
# Copyright Stefan Gofferje
#
# Licensed under the Gnu General Public License Version 3 or higher (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at https://www.gnu.org/licenses/gpl-3.0.en.html

"""Database models and session management for AIS data."""

from datetime import datetime
from typing import AsyncGenerator, Optional

from sqlalchemy import DateTime, Float, Integer, String, create_engine
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from ais_recorder.config import settings

DB_URL = (
    f"mysql+aiomysql://{settings.mariadb_user}:{settings.mariadb_password}"
    f"@{settings.mariadb_host}:{settings.mariadb_port}/{settings.mariadb_database}"
)

engine = create_async_engine(DB_URL)
ASYNC_SESSION_LOCAL = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

SYNC_DB_URL = (
    f"mysql+mysqlconnector://{settings.mariadb_user}:{settings.mariadb_password}"
    f"@{settings.mariadb_host}:{settings.mariadb_port}/{settings.mariadb_database}"
)

sync_engine = create_engine(SYNC_DB_URL)


class Base(DeclarativeBase):  # pylint: disable=too-few-public-methods
    """Base class for SQLAlchemy models."""


class Position(Base):  # pylint: disable=too-few-public-methods
    """Table for historical AIS position data."""

    __tablename__ = "positions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime, index=True)
    mmsi: Mapped[int] = mapped_column(Integer, index=True)
    vessel_name: Mapped[Optional[str]] = mapped_column(String(255))
    latitude: Mapped[float] = mapped_column(Float)
    longitude: Mapped[float] = mapped_column(Float)


class Metadata(Base):  # pylint: disable=too-few-public-methods
    """Table for vessel metadata."""

    __tablename__ = "metadata"

    mmsi: Mapped[int] = mapped_column(Integer, primary_key=True)
    imo: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    last_seen: Mapped[datetime] = mapped_column(DateTime)


async def init_db() -> None:
    """Initialize the database tables."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Get an async database session."""
    async with ASYNC_SESSION_LOCAL() as session:
        try:
            yield session
        finally:
            await session.close()
