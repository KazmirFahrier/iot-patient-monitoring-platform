from __future__ import annotations

from fastapi import APIRouter, Depends, Request
from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from iot_monitoring.dependencies import get_session
from iot_monitoring.models import TelemetryRecord
from iot_monitoring.schemas import AmbientPayload, TelemetryRead, VitalsPayload
from iot_monitoring.schemas import MedicineBoxPayload
from iot_monitoring.services.telemetry import (
    TelemetryServiceContext,
    record_ambient,
    record_medicine_box,
    record_vitals,
)

router = APIRouter(tags=["telemetry"])


@router.post("/telemetry/vitals")
async def ingest_vitals(
    payload: VitalsPayload,
    request: Request,
    session: Session = Depends(get_session),
) -> dict:
    context = TelemetryServiceContext(
        notifier=request.app.state.context.notifier,
        realtime=request.app.state.context.realtime,
    )
    record, alerts = record_vitals(session, payload, context)
    await request.app.state.context.realtime.broadcast(
        "telemetry.vitals",
        {"id": record.id, "device_key": payload.device_key, "payload": record.payload},
    )
    for alert in alerts:
        await request.app.state.context.realtime.broadcast(
            "alert.created",
            {
                "id": alert.id,
                "device_key": alert.device.device_key,
                "severity": alert.severity.value,
                "title": alert.title,
                "message": alert.message,
            },
        )
    return {"ok": True, "record_id": record.id, "alerts_created": len(alerts)}


@router.post("/telemetry/ambient")
async def ingest_ambient(
    payload: AmbientPayload,
    request: Request,
    session: Session = Depends(get_session),
) -> dict:
    context = TelemetryServiceContext(
        notifier=request.app.state.context.notifier,
        realtime=request.app.state.context.realtime,
    )
    record, alerts = record_ambient(session, payload, context)
    await request.app.state.context.realtime.broadcast(
        "telemetry.ambient",
        {"id": record.id, "device_key": payload.device_key, "payload": record.payload},
    )
    for alert in alerts:
        await request.app.state.context.realtime.broadcast(
            "alert.created",
            {
                "id": alert.id,
                "device_key": alert.device.device_key,
                "severity": alert.severity.value,
                "title": alert.title,
                "message": alert.message,
            },
        )
    return {"ok": True, "record_id": record.id, "alerts_created": len(alerts)}


@router.post("/telemetry/medicine-box")
async def ingest_medicine_box(
    payload: MedicineBoxPayload,
    request: Request,
    session: Session = Depends(get_session),
) -> dict:
    context = TelemetryServiceContext(
        notifier=request.app.state.context.notifier,
        realtime=request.app.state.context.realtime,
    )
    record, alerts = record_medicine_box(session, payload, context)
    await request.app.state.context.realtime.broadcast(
        "telemetry.medicine_box",
        {"id": record.id, "device_key": payload.device_key, "payload": record.payload},
    )
    for alert in alerts:
        await request.app.state.context.realtime.broadcast(
            "alert.created",
            {
                "id": alert.id,
                "device_key": alert.device.device_key,
                "severity": alert.severity.value,
                "title": alert.title,
                "message": alert.message,
            },
        )
    return {"ok": True, "record_id": record.id, "alerts_created": len(alerts)}


@router.get("/telemetry/recent", response_model=list[TelemetryRead])
def recent_telemetry(session: Session = Depends(get_session), limit: int = 20) -> list[TelemetryRead]:
    records = session.scalars(
        select(TelemetryRecord).order_by(desc(TelemetryRecord.recorded_at)).limit(limit)
    ).all()
    return [
        TelemetryRead(
            id=record.id,
            category=record.category,
            recorded_at=record.recorded_at,
            payload=dict(record.payload),
            device_key=record.device.device_key,
            device_name=record.device.name,
            device_type=record.device.type,
            patient_name=record.device.patient_name,
        )
        for record in records
    ]
