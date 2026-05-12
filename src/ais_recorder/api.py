# src/ais_recorder/api.py from https://github.com/sgofferj/python-ais-recorder
#
# Copyright Stefan Gofferje
#
# Licensed under the Gnu General Public License Version 3 or higher (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at https://www.gnu.org/licenses/gpl-3.0.en.html

"""REST API for querying AIS data."""

from datetime import datetime
from typing import List, Optional, Sequence

from fastapi import Depends, FastAPI, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ais_recorder.database import Metadata, Position, get_db
from ais_recorder.schemas import HealthResponse, PositionResponse, VesselResponse

app = FastAPI(title="AIS Recorder API")

logger = __import__("structlog").get_logger()


@app.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """Health check endpoint for Docker/Kubernetes."""
    return HealthResponse(status="healthy", version="0.2.0")


@app.get("/positions", response_model=List[PositionResponse])
async def query_positions(  # pylint: disable=too-many-arguments,too-many-positional-arguments
    mmsi: Optional[int] = None,
    imo: Optional[int] = None,
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
    bbox: Optional[str] = Query(None, description="BBox format: min_lon,min_lat,max_lon,max_lat"),
    db: AsyncSession = Depends(get_db),
) -> Sequence[Position]:
    """Query historical AIS positions with various filters."""
    stmt = select(Position)

    if imo is not None:
        stmt = stmt.join(Metadata, Position.mmsi == Metadata.mmsi).where(Metadata.imo == imo)

    if mmsi is not None:
        stmt = stmt.where(Position.mmsi == mmsi)

    if start_time:
        stmt = stmt.where(Position.timestamp >= start_time)
    if end_time:
        stmt = stmt.where(Position.timestamp <= end_time)

    if bbox:
        try:
            min_lon, min_lat, max_lon, max_lat = map(float, bbox.split(","))
            stmt = stmt.where(
                Position.longitude >= min_lon,
                Position.longitude <= max_lon,
                Position.latitude >= min_lat,
                Position.latitude <= max_lat,
            )
        except ValueError as exc:
            raise HTTPException(
                status_code=400, detail="Invalid bbox format. Expected min_lon,min_lat,max_lon,max_lat"
            ) from exc

    stmt = stmt.order_by(Position.timestamp.desc())
    result = await db.execute(stmt)
    positions = result.scalars().all()

    return positions


@app.get("/vessels", response_model=List[VesselResponse])
async def list_vessels(db: AsyncSession = Depends(get_db)) -> Sequence[Metadata]:
    """List all vessels in the metadata table."""
    stmt = select(Metadata)
    result = await db.execute(stmt)
    vessels = result.scalars().all()
    return vessels
