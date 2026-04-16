from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from iot_monitoring.models import AlertSeverity, AlertStatus, DeviceType


def _default_recorded_at() -> datetime:
    return datetime.now(timezone.utc)


class DeviceRegistration(BaseModel):
    device_key: str = Field(min_length=3, max_length=80)
    name: str = Field(min_length=3, max_length=120)
    type: DeviceType
    patient_name: str | None = None
    location_label: str | None = None
    description: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class DeviceRead(DeviceRegistration):
    id: int
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        validation_alias="metadata_json",
    )
    last_seen_at: datetime | None = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


class VitalsPayload(BaseModel):
    device_key: str
    recorded_at: datetime = Field(default_factory=_default_recorded_at)
    heart_rate_bpm: float = Field(ge=0, le=260)
    spo2_percent: float = Field(ge=0, le=100)
    body_temperature_c: float = Field(ge=20, le=45)
    systolic_bp: int | None = Field(default=None, ge=50, le=260)
    diastolic_bp: int | None = Field(default=None, ge=20, le=180)
    signal_quality: Literal["excellent", "good", "fair", "poor"] = "good"


class AmbientPayload(BaseModel):
    device_key: str
    recorded_at: datetime = Field(default_factory=_default_recorded_at)
    room_temperature_c: float = Field(ge=-20, le=80)
    humidity_percent: float = Field(ge=0, le=100)
    pressure_hpa: float = Field(ge=300, le=1200)
    smoke_detected: bool = False
    flame_detected: bool = False
    latitude: float | None = Field(default=None, ge=-90, le=90)
    longitude: float | None = Field(default=None, ge=-180, le=180)


class MedicineBoxPayload(BaseModel):
    device_key: str
    recorded_at: datetime = Field(default_factory=_default_recorded_at)
    uid: str = Field(min_length=4, max_length=64)
    authorized: bool
    action: Literal["unlock_attempt", "unlock_success", "inventory_reminder", "forced_open"]
    notes: str | None = None


class TelemetryRead(BaseModel):
    id: int
    category: str
    recorded_at: datetime
    payload: dict[str, Any]
    device_key: str
    device_name: str
    device_type: DeviceType
    patient_name: str | None = None


class AlertRead(BaseModel):
    id: int
    device_key: str
    device_name: str
    severity: AlertSeverity
    status: AlertStatus
    title: str
    message: str
    channels: list[str]
    context: dict[str, Any]
    created_at: datetime
    acknowledged_at: datetime | None = None


class AcknowledgeAlertResponse(BaseModel):
    id: int
    status: AlertStatus
    acknowledged_at: datetime


class DashboardStats(BaseModel):
    total_devices: int
    active_alerts: int
    critical_alerts: int
    average_heart_rate_bpm: float | None
    average_spo2_percent: float | None


class DashboardSnapshot(BaseModel):
    generated_at: datetime
    stats: DashboardStats
    devices: list[DeviceRead]
    alerts: list[AlertRead]
    recent_events: list[TelemetryRead]
    vitals_trend: list[dict[str, Any]]
    ambient_trend: list[dict[str, Any]]


class EventEnvelope(BaseModel):
    event: str
    payload: dict[str, Any]

    @field_validator("payload")
    @classmethod
    def ensure_mapping(cls, value: dict[str, Any]) -> dict[str, Any]:
        return value
