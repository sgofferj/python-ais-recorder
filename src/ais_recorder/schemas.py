# src/ais_recorder/schemas.py from https://github.com/sgofferj/python-ais-recorder
#
# Copyright Stefan Gofferje
#
# Licensed under the Gnu General Public License Version 3 or higher (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at https://www.gnu.org/licenses/gpl-3.0.en.html

"""Pydantic schemas for the AIS Recorder API."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


class HealthResponse(BaseModel):
    """Schema for health check response."""

    status: str
    version: str


class PositionResponse(BaseModel):
    """Schema for AIS position data in API responses."""

    timestamp: datetime
    mmsi: int = Field(..., ge=100000000, le=999999999)
    vessel_name: Optional[str] = Field(None, max_length=255)
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)

    model_config = ConfigDict(from_attributes=True)


class VesselResponse(BaseModel):
    """Schema for vessel metadata in API responses."""

    mmsi: int = Field(..., ge=100000000, le=999999999)
    imo: Optional[int] = Field(None, ge=1000000, le=9999999)
    last_seen: datetime

    model_config = ConfigDict(from_attributes=True)


class AISLocationPayload(BaseModel):
    """Schema for validating incoming AIS location data."""

    timestamp: str
    location: dict[str, object] = Field(..., alias="location")

    @field_validator("timestamp")
    @classmethod
    def validate_timestamp(cls, v: str) -> str:
        if not v.endswith("Z"):
            v = v + "Z"
        datetime.fromisoformat(v.replace("Z", ""))
        return v


class AISMetadataPayload(BaseModel):
    """Schema for validating incoming AIS metadata."""

    name: Optional[str] = Field(None, max_length=255)
    imo: Optional[int] = Field(None, ge=1000000, le=9999999)
    mmsi: Optional[int] = Field(None, ge=100000000, le=999999999)
