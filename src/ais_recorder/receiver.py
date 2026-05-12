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
from typing import Any, Dict

import paho.mqtt.client as mqtt
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ais_recorder.config import settings
from ais_recorder.database import ASYNC_SESSION_LOCAL, Metadata, Position

logger = __import__("structlog").get_logger()


class AISReceiver:
    """Receiver class to handle MQTT connection and message processing."""

    def __init__(self) -> None:
        """Initialize the MQTT client."""
        self.client = mqtt.Client(
            callback_api_version=mqtt.CallbackAPIVersion.VERSION2,  # type: ignore[attr-defined]
            transport="websockets",
        )
        self.client.ws_set_options(headers={"Digitraffic-User": settings.digitraffic_user})
        self.client.tls_set(cert_reqs=ssl.CERT_REQUIRED)
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message

    def on_connect(
        self, _client: mqtt.Client, _userdata: Any, _flags: Dict[str, Any], rc: int, _properties: Any = None
    ) -> None:
        """Handle MQTT connection."""
        if rc == 0:
            logger.info("Connected to Digitraffic MQTT")
            self.client.subscribe("vessels/+/location")
            self.client.subscribe("vessels/+/metadata")
        else:
            logger.error("Failed to connect to MQTT, return code %d", rc)

    def on_message(self, _client: mqtt.Client, _userdata: Any, msg: mqtt.MQTTMessage) -> None:
        """Process incoming MQTT messages."""
        asyncio.create_task(self._process_message(msg))

    async def _process_message(self, msg: mqtt.MQTTMessage) -> None:
        """Process incoming MQTT message asynchronously."""
        try:
            payload: Dict[str, Any] = json.loads(msg.payload.decode())
            topic_parts = msg.topic.split("/")
            mmsi = int(topic_parts[1])
            message_type = topic_parts[2]

            async with ASYNC_SESSION_LOCAL() as db:
                if message_type == "location":
                    await self._handle_location(db, mmsi, payload)
                elif message_type == "metadata":
                    await self._handle_metadata(db, mmsi, payload)
                await db.commit()
        except json.JSONDecodeError as e:
            logger.error("Error decoding JSON from topic %s: %s", msg.topic, e)
        except Exception as e:  # pylint: disable=broad-exception-caught
            logger.error("Error processing message on topic %s: %s", msg.topic, e)

    async def _handle_location(self, db: AsyncSession, mmsi: int, payload: Dict[str, Any]) -> None:
        """Save position data to the database."""
        timestamp_str = payload.get("timestamp")
        if not isinstance(timestamp_str, str):
            logger.warning("Missing or invalid timestamp in location payload for MMSI %d", mmsi)
            return

        if timestamp_str.endswith("Z"):
            timestamp_str = timestamp_str[:-1]
        timestamp = datetime.fromisoformat(timestamp_str)

        coords = payload.get("location", {}).get("coordinates", [0.0, 0.0])

        new_pos = Position(
            timestamp=timestamp,
            mmsi=mmsi,
            latitude=float(coords[1]),
            longitude=float(coords[0]),
        )
        db.add(new_pos)

        stmt = select(Metadata).where(Metadata.mmsi == mmsi)
        result = await db.execute(stmt)
        meta = result.scalars().first()
        if meta:
            meta.last_seen = timestamp
        else:
            db.add(Metadata(mmsi=mmsi, last_seen=timestamp))

    async def _handle_metadata(self, db: AsyncSession, mmsi: int, payload: Dict[str, Any]) -> None:
        """Save vessel metadata to the database."""
        imo = payload.get("imo")
        timestamp = datetime.now()

        stmt = select(Metadata).where(Metadata.mmsi == mmsi)
        result = await db.execute(stmt)
        meta = result.scalars().first()
        if meta:
            if isinstance(imo, int):
                meta.imo = imo
            meta.last_seen = timestamp
        else:
            db.add(Metadata(mmsi=mmsi, imo=imo if isinstance(imo, int) else None, last_seen=timestamp))

    def run(self) -> None:
        """Start the MQTT client loop."""
        self.client.connect(settings.digitraffic_mqtt_url, settings.digitraffic_mqtt_port, 60)
        self.client.loop_forever()


if __name__ == "__main__":
    receiver = AISReceiver()
    receiver.run()
