from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from iot_monitoring.models import Device, DeviceType


def seed_demo_devices(session: Session) -> None:
    existing = session.scalar(select(Device.id).limit(1))
    if existing:
        return

    devices = [
        Device(
            device_key="patient-kit-01",
            name="Patient Monitoring Kit 01",
            type=DeviceType.patient_monitor,
            patient_name="Amina Rahman",
            location_label="Ward A / Bed 4",
            description="Vital-sign kit with MAX30102, temperature probe, and BP support.",
            metadata_json={"sensors": ["MAX30102", "DS18B20", "BP cuff"]},
        ),
        Device(
            device_key="ambient-node-01",
            name="Ambient Monitoring Node 01",
            type=DeviceType.ambient_monitor,
            patient_name="Amina Rahman",
            location_label="Ward A / Bed 4",
            description="Room safety node with BMP180, DHT11, smoke, flame, and GPS signals.",
            metadata_json={"sensors": ["DHT11", "BMP180", "MQ2", "Flame Sensor", "NEO-6M"]},
        ),
        Device(
            device_key="medbox-01",
            name="Secured Medicine Box 01",
            type=DeviceType.medicine_box,
            patient_name="Amina Rahman",
            location_label="Ward A / Medication Shelf",
            description="RFID/NFC protected medicine cabinet with access auditing.",
            metadata_json={"access": ["RFID", "NFC", "Solenoid Lock"]},
        ),
    ]

    session.add_all(devices)
    session.commit()
