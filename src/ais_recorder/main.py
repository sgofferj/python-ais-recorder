# src/ais_recorder/main.py from https://github.com/sgofferj/python-ais-recorder
#
# Copyright Stefan Gofferje
#
# Licensed under the Gnu General Public License Version 3 or higher (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at https://www.gnu.org/licenses/gpl-3.0.en.html

"""Main orchestrator for the AIS Recorder."""

import asyncio
import multiprocessing
import signal
import sys
import time
from typing import Any, List

import uvicorn
import structlog

from ais_recorder.api import app
from ais_recorder.config import settings
from ais_recorder.database import init_db
from ais_recorder.receiver import AISReceiver
from ais_recorder.retention import run_retention_worker


def configure_logging() -> None:
    """Configure structured logging for JSON output (Loki compatible)."""
    structlog.configure(
        processors=[
            structlog.stdlib.add_log_level,
            structlog.stdlib.add_logger_name,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.JSONRenderer(),
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )


def run_api() -> None:
    """Run the FastAPI application."""
    configure_logging()
    logger = structlog.get_logger()
    logger.info("Starting API worker(s)")
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        workers=settings.api_workers,
        log_level="info",
        log_config=None,
    )


def run_receiver() -> None:
    """Run the AIS data receiver."""
    configure_logging()
    logger = structlog.get_logger()
    logger.info("Starting AIS receiver worker")
    receiver = AISReceiver()
    asyncio.run(receiver.run())


def run_retention() -> None:
    """Run the data retention cleanup worker."""
    configure_logging()
    logger = structlog.get_logger()
    logger.info("Starting retention worker")
    asyncio.run(run_retention_worker())


def main() -> None:
    """Initialize database and start all workers."""
    configure_logging()
    logger = structlog.get_logger()
    logger.info("Initializing AIS Recorder")

    try:
        asyncio.run(init_db())
    except Exception as e:  # pylint: disable=broad-exception-caught
        logger.error("Failed to initialize database: %s", e)

    processes: List[multiprocessing.Process] = []

    workers = [
        run_receiver,
        run_retention,
        run_api,
    ]

    for worker_func in workers:
        p = multiprocessing.Process(target=worker_func)
        p.start()
        processes.append(p)

    def signal_handler(_sig: int, _frame: Any) -> None:
        logger.info("Termination signal received. Shutting down...")
        for p in processes:
            p.terminate()
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    while True:
        time.sleep(1)


if __name__ == "__main__":
    main()
