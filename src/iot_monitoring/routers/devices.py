from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from iot_monitoring.dependencies import get_session
from iot_monitoring.models import Device
from iot_monitoring.schemas import DeviceRead, DeviceRegistration

router = APIRouter(tags=["devices"])


@router.get("/devices", response_model=list[DeviceRead])
def list_devices(session: Session = Depends(get_session)) -> list[Device]:
    return session.scalars(select(Device).order_by(Device.name)).all()


@router.post("/devices/register", response_model=DeviceRead, status_code=201)
def register_device(payload: DeviceRegistration, session: Session = Depends(get_session)) -> Device:
    existing = session.scalar(select(Device).where(Device.device_key == payload.device_key))
    if existing:
        raise HTTPException(status_code=409, detail="Device key already exists.")

    device = Device(
        device_key=payload.device_key,
        name=payload.name,
        type=payload.type,
        patient_name=payload.patient_name,
        location_label=payload.location_label,
        description=payload.description,
        metadata_json=payload.metadata,
    )
    session.add(device)
    session.commit()
    session.refresh(device)
    return device
