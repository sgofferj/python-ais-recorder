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

from sqlalchemy import DateTime, Float, Integer, String, create_engine, text
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from ais_recorder.config import settings

DB_URL = settings.mariadb_url

# Lazy-initialized engine and sessionmaker
_ASYNC_ENGINE: Optional[AsyncEngine] = None
_ASYNC_SESSION_MAKER: Optional[async_sessionmaker[AsyncSession]] = None


def get_async_session_maker() -> async_sessionmaker[AsyncSession]:
    """Get or create the async session maker."""
    global _ASYNC_ENGINE, _ASYNC_SESSION_MAKER  # pylint: disable=global-statement
    if _ASYNC_SESSION_MAKER is None:
        _ASYNC_ENGINE = create_async_engine(DB_URL)
        _ASYNC_SESSION_MAKER = async_sessionmaker(_ASYNC_ENGINE, class_=AsyncSession, expire_on_commit=False)
    return _ASYNC_SESSION_MAKER


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
    latitude: Mapped[float] = mapped_column(Float)
    longitude: Mapped[float] = mapped_column(Float)


class Metadata(Base):  # pylint: disable=too-few-public-methods
    """Table for vessel metadata."""

    __tablename__ = "metadata"

    mmsi: Mapped[int] = mapped_column(Integer, primary_key=True)
    imo: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    vessel_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    last_seen: Mapped[datetime] = mapped_column(DateTime)


async def init_db() -> None:
    """Initialize the database tables and ensure schema is up to date."""
    # Use a temporary engine to avoid binding the global one to the main process loop
    temp_engine = create_async_engine(DB_URL)
    async with temp_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

        # Manually ensure schema updates that Base.metadata.create_all (IF NOT EXISTS) misses
        # Add vessel_name to metadata if it doesn't exist
        await conn.execute(text("ALTER TABLE metadata ADD COLUMN IF NOT EXISTS vessel_name VARCHAR(255) AFTER imo;"))
        # Remove vessel_name from positions if it exists
        await conn.execute(text("ALTER TABLE positions DROP COLUMN IF EXISTS vessel_name;"))

    await temp_engine.dispose()


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Get an async database session."""
    session_maker = get_async_session_maker()
    async with session_maker() as session:
        try:
            yield session
        finally:
            await session.close()
