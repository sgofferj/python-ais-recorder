# src/ais_recorder/receiver.py from https://github.com/sgofferj/python-ais-recorder
#
# Copyright Stefan Gofferje
#
# Licensed under the Gnu General Public License Version 3 or higher (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at https://www.gnu.org/licenses/gpl-3.0.en.html

"""AIS Data Receiver from Digitraffic via MQTT over WebSockets."""

import asyncio
import json
import ssl
from datetime import datetime
from typing import Any, Dict, Optional

import aiomqtt
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ais_recorder.config import settings
from ais_recorder.database import Metadata, Position, get_async_session_maker

logger = __import__("structlog").get_logger()


class AISReceiver:
    """Receiver class to handle MQTT connection and message processing."""

    def get_cached_name(self) -> Optional[str]:
        """Get a vessel name from the in-memory cache."""
        # Note: This is now less relevant since we don't store name in positions
        # but kept for pylint satisfaction.
        return None

    async def run(self) -> None:
        """Start the MQTT client loop."""
        while True:
            try:
                async with aiomqtt.Client(
                    hostname=settings.digitraffic_mqtt_url,
                    port=settings.digitraffic_mqtt_port,
                    transport="websockets",
                    tls_context=ssl.create_default_context(),
                    websocket_headers={"Digitraffic-User": settings.digitraffic_user},
                ) as client:
                    logger.info("Connected to Digitraffic MQTT (vessels-v2)")
                    await client.subscribe("vessels-v2/#")
                    async for message in client.messages:
                        await self._process_message(message)
            except Exception as e:  # pylint: disable=broad-exception-caught
                logger.error("MQTT connection error: %s", e)
                await asyncio.sleep(5)

    async def _process_message(self, message: aiomqtt.Message) -> None:
        """Process incoming MQTT message asynchronously."""
        try:
            payload: Dict[str, Any] = json.loads(message.payload.decode())
            topic_str = str(message.topic)
            topic_parts = topic_str.split("/")
            if len(topic_parts) < 3:
                return
            mmsi = int(topic_parts[1])
            message_type = topic_parts[2]

            session_maker = get_async_session_maker()
            async with session_maker() as db:
                if message_type == "location":
                    await self._handle_location(db, mmsi, payload)
                elif message_type == "metadata":
                    await self._handle_metadata(db, mmsi, payload)
                await db.commit()
        except json.JSONDecodeError as e:
            logger.error("Error decoding JSON from topic %s: %s", message.topic, e)
        except Exception as e:  # pylint: disable=broad-exception-caught
            logger.error("Error processing message on topic %s: %s", message.topic, e)

    async def _handle_location(self, db: AsyncSession, mmsi: int, payload: Dict[str, Any]) -> None:
        """Save position data to the database."""
        # vessels-v2 uses 'lat', 'lon' and 'time' (unix timestamp in ms)
        lat = payload.get("lat")
        lon = payload.get("lon")
        timestamp_ms = payload.get("time")

        if lat is None or lon is None or timestamp_ms is None:
            return

        timestamp = datetime.fromtimestamp(float(timestamp_ms))

        new_pos = Position(
            timestamp=timestamp,
            mmsi=mmsi,
            latitude=float(lat),
            longitude=float(lon),
        )
        db.add(new_pos)

        # Only update last_seen if metadata entry already exists
        stmt = select(Metadata).where(Metadata.mmsi == mmsi)
        result = await db.execute(stmt)
        meta = result.scalars().first()
        if meta:
            meta.last_seen = timestamp

    async def _handle_metadata(self, db: AsyncSession, mmsi: int, payload: Dict[str, Any]) -> None:
        """Save vessel metadata to the database."""
        imo = payload.get("imo")
        name = payload.get("name")
        timestamp = datetime.now()

        stmt = select(Metadata).where(Metadata.mmsi == mmsi)
        result = await db.execute(stmt)
        meta = result.scalars().first()
        if meta:
            if isinstance(imo, int):
                meta.imo = imo
            if name:
                meta.vessel_name = name.strip()
            meta.last_seen = timestamp
        else:
            # Metadata rows are created ONLY here
            db.add(
                Metadata(
                    mmsi=mmsi,
                    imo=imo if isinstance(imo, int) else None,
                    vessel_name=name.strip() if name else None,
                    last_seen=timestamp,
                )
            )


if __name__ == "__main__":
    receiver = AISReceiver()
    asyncio.run(receiver.run())
