from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from sqlalchemy import desc, func, select
from sqlalchemy.orm import Session

from iot_monitoring.models import Alert, AlertSeverity, AlertStatus, Device, TelemetryRecord
from iot_monitoring.schemas import AlertRead, DashboardSnapshot, DashboardStats, DeviceRead, TelemetryRead


def build_dashboard_snapshot(session: Session) -> DashboardSnapshot:
    devices = session.scalars(select(Device).order_by(Device.name)).all()
    alerts = session.scalars(select(Alert).order_by(desc(Alert.created_at)).limit(12)).all()
    recent_events = session.scalars(
        select(TelemetryRecord).order_by(desc(TelemetryRecord.recorded_at)).limit(20)
    ).all()
    vitals_trend_records = session.scalars(
        select(TelemetryRecord)
        .where(TelemetryRecord.category == "vitals")
        .order_by(desc(TelemetryRecord.recorded_at))
        .limit(16)
    ).all()
    ambient_trend_records = session.scalars(
        select(TelemetryRecord)
        .where(TelemetryRecord.category == "ambient")
        .order_by(desc(TelemetryRecord.recorded_at))
        .limit(16)
    ).all()

    heart_rate_values = [
        record.payload["heart_rate_bpm"]
        for record in vitals_trend_records
        if isinstance(record.payload.get("heart_rate_bpm"), (int, float))
    ]
    spo2_values = [
        record.payload["spo2_percent"]
        for record in vitals_trend_records
        if isinstance(record.payload.get("spo2_percent"), (int, float))
    ]
    active_alerts = session.scalar(
        select(func.count(Alert.id)).where(Alert.status == AlertStatus.open)
    ) or 0
    critical_alerts = session.scalar(
        select(func.count(Alert.id)).where(
            Alert.status == AlertStatus.open, Alert.severity == AlertSeverity.critical
        )
    ) or 0

    return DashboardSnapshot(
        generated_at=datetime.now(timezone.utc),
        stats=DashboardStats(
            total_devices=len(devices),
            active_alerts=active_alerts,
            critical_alerts=critical_alerts,
            average_heart_rate_bpm=(
                sum(heart_rate_values) / len(heart_rate_values) if heart_rate_values else None
            ),
            average_spo2_percent=sum(spo2_values) / len(spo2_values) if spo2_values else None,
        ),
        devices=[DeviceRead.model_validate(device) for device in devices],
        alerts=[_serialize_alert(alert) for alert in alerts],
        recent_events=[_serialize_event(record) for record in recent_events],
        vitals_trend=[_trend_point(record) for record in reversed(vitals_trend_records)],
        ambient_trend=[_trend_point(record) for record in reversed(ambient_trend_records)],
    )


def _serialize_alert(alert: Alert) -> AlertRead:
    return AlertRead(
        id=alert.id,
        device_key=alert.device.device_key,
        device_name=alert.device.name,
        severity=alert.severity,
        status=alert.status,
        title=alert.title,
        message=alert.message,
        channels=list(alert.channels),
        context=dict(alert.context_json),
        created_at=alert.created_at,
        acknowledged_at=alert.acknowledged_at,
    )


def _serialize_event(record: TelemetryRecord) -> TelemetryRead:
    return TelemetryRead(
        id=record.id,
        category=record.category,
        recorded_at=record.recorded_at,
        payload=dict(record.payload),
        device_key=record.device.device_key,
        device_name=record.device.name,
        device_type=record.device.type,
        patient_name=record.device.patient_name,
    )


def _trend_point(record: TelemetryRecord) -> dict[str, Any]:
    point = {"recorded_at": record.recorded_at.isoformat(), **record.payload}
    point["device_name"] = record.device.name
    return point
