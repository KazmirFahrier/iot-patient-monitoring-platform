from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from typing import Any

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from iot_monitoring.models import Alert, AlertStatus, Device, TelemetryRecord
from iot_monitoring.schemas import AmbientPayload, MedicineBoxPayload, VitalsPayload
from iot_monitoring.services.notifications import NotificationService
from iot_monitoring.services.realtime import RealtimeManager
from iot_monitoring.services.rules import (
    RuleHit,
    evaluate_ambient,
    evaluate_medicine_box,
    evaluate_vitals,
)


@dataclass(slots=True)
class TelemetryServiceContext:
    notifier: NotificationService
    realtime: RealtimeManager


def record_vitals(
    session: Session,
    payload: VitalsPayload,
    context: TelemetryServiceContext,
) -> tuple[TelemetryRecord, list[Alert]]:
    return _record_generic(
        session=session,
        category="vitals",
        device_key=payload.device_key,
        recorded_at=payload.recorded_at,
        payload=payload.model_dump(mode="json"),
        evaluate=evaluate_vitals,
        context=context,
    )


def record_ambient(
    session: Session,
    payload: AmbientPayload,
    context: TelemetryServiceContext,
) -> tuple[TelemetryRecord, list[Alert]]:
    return _record_generic(
        session=session,
        category="ambient",
        device_key=payload.device_key,
        recorded_at=payload.recorded_at,
        payload=payload.model_dump(mode="json"),
        evaluate=evaluate_ambient,
        context=context,
    )


def record_medicine_box(
    session: Session,
    payload: MedicineBoxPayload,
    context: TelemetryServiceContext,
) -> tuple[TelemetryRecord, list[Alert]]:
    return _record_generic(
        session=session,
        category="medicine_box",
        device_key=payload.device_key,
        recorded_at=payload.recorded_at,
        payload=payload.model_dump(mode="json"),
        evaluate=evaluate_medicine_box,
        context=context,
    )


def _record_generic(
    session: Session,
    category: str,
    device_key: str,
    recorded_at: datetime,
    payload: dict[str, Any],
    evaluate,
    context: TelemetryServiceContext,
) -> tuple[TelemetryRecord, list[Alert]]:
    device = session.scalar(select(Device).where(Device.device_key == device_key))
    if not device:
        raise HTTPException(status_code=404, detail=f"Device '{device_key}' is not registered.")

    record = TelemetryRecord(
        device=device,
        category=category,
        recorded_at=_ensure_utc(recorded_at),
        payload=payload,
    )
    device.last_seen_at = utc_now()
    session.add(record)

    alert_models = []
    for hit in evaluate(payload, device.name, device.patient_name):
        alert = Alert(
            device=device,
            severity=hit.severity,
            status=AlertStatus.open,
            title=hit.title,
            message=hit.message,
            channels=hit.channels,
            context_json=hit.context,
        )
        session.add(alert)
        alert_models.append(alert)

    session.commit()
    session.refresh(record)

    for alert in alert_models:
        session.refresh(alert)
        context.notifier.dispatch_for_alert(session, alert)
    session.commit()

    return record, alert_models


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _ensure_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)
