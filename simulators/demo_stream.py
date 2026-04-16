from __future__ import annotations

import random
import time
from datetime import datetime, timezone

import httpx

BASE_URL = "http://127.0.0.1:8000"


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def maybe_spike(value: float, normal_delta: float, spike_delta: float, chance: float = 0.12) -> float:
    if random.random() < chance:
        return value + random.choice([-1, 1]) * spike_delta
    return value + random.uniform(-normal_delta, normal_delta)


def register_devices(client: httpx.Client) -> None:
    devices = [
        {
            "device_key": "patient-kit-01",
            "name": "Patient Monitoring Kit 01",
            "type": "patient_monitor",
            "patient_name": "Amina Rahman",
            "location_label": "Ward A / Bed 4",
            "metadata": {"simulated": True},
        },
        {
            "device_key": "ambient-node-01",
            "name": "Ambient Monitoring Node 01",
            "type": "ambient_monitor",
            "patient_name": "Amina Rahman",
            "location_label": "Ward A / Bed 4",
            "metadata": {"simulated": True},
        },
        {
            "device_key": "medbox-01",
            "name": "Secured Medicine Box 01",
            "type": "medicine_box",
            "patient_name": "Amina Rahman",
            "location_label": "Ward A / Medication Shelf",
            "metadata": {"simulated": True},
        },
    ]

    for device in devices:
        response = client.post(f"{BASE_URL}/api/devices/register", json=device)
        if response.status_code not in (201, 409):
            response.raise_for_status()


def stream() -> None:
    heart_rate = 82.0
    spo2 = 98.0
    body_temp = 36.9
    room_temp = 27.0
    humidity = 58.0
    pressure = 1012.0

    with httpx.Client(timeout=5) as client:
        register_devices(client)
        print("Streaming demo telemetry to", BASE_URL)
        while True:
            heart_rate = maybe_spike(heart_rate, 5, 58)
            spo2 = max(84.0, min(100.0, maybe_spike(spo2, 1.3, 7.5)))
            body_temp = max(35.4, min(40.5, maybe_spike(body_temp, 0.18, 2.4)))
            room_temp = max(24.0, min(39.0, maybe_spike(room_temp, 0.5, 9.0, chance=0.08)))
            humidity = max(38.0, min(88.0, maybe_spike(humidity, 2.0, 10.0, chance=0.07)))
            pressure = max(985.0, min(1035.0, maybe_spike(pressure, 1.1, 9.0, chance=0.05)))

            vitals_payload = {
                "device_key": "patient-kit-01",
                "recorded_at": now(),
                "heart_rate_bpm": round(heart_rate, 1),
                "spo2_percent": round(spo2, 1),
                "body_temperature_c": round(body_temp, 1),
                "systolic_bp": int(random.randint(112, 145)),
                "diastolic_bp": int(random.randint(72, 96)),
                "signal_quality": random.choice(["excellent", "good", "good", "fair"]),
            }
            ambient_payload = {
                "device_key": "ambient-node-01",
                "recorded_at": now(),
                "room_temperature_c": round(room_temp, 1),
                "humidity_percent": round(humidity, 1),
                "pressure_hpa": round(pressure, 1),
                "smoke_detected": random.random() < 0.05,
                "flame_detected": random.random() < 0.03,
                "latitude": 23.8103,
                "longitude": 90.4125,
            }
            medbox_payload = {
                "device_key": "medbox-01",
                "recorded_at": now(),
                "uid": random.choice(["A1B2C3D4", "F0E1D2C3", "UNKNOWN-UID"]),
                "authorized": random.random() > 0.12,
                "action": random.choices(
                    ["unlock_success", "unlock_attempt", "inventory_reminder", "forced_open"],
                    weights=[0.62, 0.18, 0.12, 0.08],
                    k=1,
                )[0],
                "notes": "Demo stream event",
            }

            for endpoint, payload in (
                ("/api/telemetry/vitals", vitals_payload),
                ("/api/telemetry/ambient", ambient_payload),
                ("/api/telemetry/medicine-box", medbox_payload),
            ):
                response = client.post(f"{BASE_URL}{endpoint}", json=payload)
                response.raise_for_status()

            print(
                f"[{datetime.now().strftime('%H:%M:%S')}] "
                f"HR={vitals_payload['heart_rate_bpm']} "
                f"SpO2={vitals_payload['spo2_percent']} "
                f"Temp={vitals_payload['body_temperature_c']} "
                f"Ambient={ambient_payload['room_temperature_c']}"
            )
            time.sleep(2)


if __name__ == "__main__":
    stream()
