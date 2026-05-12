# src/ais_recorder/retention.py from https://github.com/sgofferj/python-ais-recorder
#
# Copyright Stefan Gofferje
#
# Licensed under the Gnu General Public License Version 3 or higher (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at https://www.gnu.org/licenses/gpl-3.0.en.html

"""Data retention cleanup worker."""

import asyncio
from datetime import datetime, timedelta

from sqlalchemy import CursorResult, delete

from apscheduler.schedulers.asyncio import AsyncIOScheduler

from ais_recorder.config import settings
from ais_recorder.database import Metadata, Position, get_async_session_maker

logger = __import__("structlog").get_logger()


async def cleanup_task() -> None:
    """Remove old data from the database."""
    logger.info("Starting data retention cleanup task")
    now = datetime.now()

    session_maker = get_async_session_maker()
    async with session_maker() as db:
        try:
            retention_limit = now - timedelta(hours=settings.retention_hours)
            # Use more efficient delete statement
            stmt = delete(Position).where(Position.timestamp < retention_limit)
            result = await db.execute(stmt)
            if isinstance(result, CursorResult):
                logger.info("Deleted %d old positions", result.rowcount)

            metadata_limit = now - timedelta(days=30)
            stmt_meta = delete(Metadata).where(Metadata.last_seen < metadata_limit)
            result_meta = await db.execute(stmt_meta)
            if isinstance(result_meta, CursorResult):
                logger.info("Deleted %d old metadata entries", result_meta.rowcount)

            await db.commit()
        except Exception as e:  # pylint: disable=broad-exception-caught
            logger.error("Error during cleanup task: %s", e)
            await db.rollback()


async def run_retention_worker() -> None:
    """Start the retention scheduler."""
    scheduler = AsyncIOScheduler()
    interval_hours = max(1, settings.retention_hours // 2)
    scheduler.add_job(cleanup_task, "interval", hours=interval_hours, next_run_time=datetime.now())
    logger.info("Retention worker started with interval %d hours", interval_hours)
    scheduler.start()

    try:
        while True:
            await asyncio.sleep(3600)
    except (KeyboardInterrupt, asyncio.CancelledError):
        scheduler.shutdown()


if __name__ == "__main__":
    asyncio.run(run_retention_worker())
