from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from iot_monitoring.dependencies import get_session
from iot_monitoring.models import Alert, AlertStatus
from iot_monitoring.schemas import AcknowledgeAlertResponse, AlertRead

router = APIRouter(tags=["alerts"])


@router.get("/alerts", response_model=list[AlertRead])
def list_alerts(session: Session = Depends(get_session), status: AlertStatus | None = None):
    statement = select(Alert).order_by(desc(Alert.created_at)).limit(50)
    if status:
        statement = statement.where(Alert.status == status)

    alerts = session.scalars(statement).all()
    return [
        AlertRead(
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
        for alert in alerts
    ]


@router.post("/alerts/{alert_id}/acknowledge", response_model=AcknowledgeAlertResponse)
def acknowledge_alert(alert_id: int, session: Session = Depends(get_session)):
    alert = session.get(Alert, alert_id)
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found.")

    alert.status = AlertStatus.acknowledged
    alert.acknowledged_at = datetime.now(timezone.utc)
    session.add(alert)
    session.commit()
    session.refresh(alert)
    return AcknowledgeAlertResponse(
        id=alert.id,
        status=alert.status,
        acknowledged_at=alert.acknowledged_at,
    )
