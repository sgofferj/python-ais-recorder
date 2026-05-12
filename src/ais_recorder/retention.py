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

from sqlalchemy import select

from apscheduler.schedulers.asyncio import AsyncIOScheduler

from ais_recorder.config import settings
from ais_recorder.database import ASYNC_SESSION_LOCAL, Metadata, Position

logger = __import__("structlog").get_logger()


async def cleanup_task() -> None:
    """Remove old data from the database."""
    logger.info("Starting data retention cleanup task")
    now = datetime.now()

    async with ASYNC_SESSION_LOCAL() as db:
        retention_limit = now - timedelta(hours=settings.retention_hours)
        stmt = select(Position).where(Position.timestamp < retention_limit)
        result = await db.execute(stmt)
        positions_to_delete = result.scalars().all()
        deleted_positions = len(positions_to_delete)
        for pos in positions_to_delete:
            await db.delete(pos)

        logger.info("Deleted %d old positions", deleted_positions)

        metadata_limit = now - timedelta(days=30)
        stmt_meta = select(Metadata).where(Metadata.last_seen < metadata_limit)
        result_meta = await db.execute(stmt_meta)
        metadata_to_delete = result_meta.scalars().all()
        deleted_metadata = len(metadata_to_delete)
        for meta in metadata_to_delete:
            await db.delete(meta)

        logger.info("Deleted %d old metadata entries", deleted_metadata)

        await db.commit()


def start_retention_worker() -> None:
    """Start the retention scheduler."""
    scheduler = AsyncIOScheduler()
    interval_hours = max(1, settings.retention_hours // 2)
    scheduler.add_job(cleanup_task, "interval", hours=interval_hours, next_run_time=datetime.now())
    logger.info("Retention worker started with interval %d hours", interval_hours)
    scheduler.start()

    try:
        asyncio.get_event_loop().run_forever()
    except (KeyboardInterrupt, SystemExit):
        logger.info("Retention worker stopped")


if __name__ == "__main__":
    start_retention_worker()
