from __future__ import annotations

from fastapi.testclient import TestClient

from iot_monitoring.app_factory import create_app
from iot_monitoring.config import Settings


def create_test_client(tmp_path):
    database_path = tmp_path / "test.db"
    settings = Settings(
        database_url=f"sqlite:///{database_path}",
        bootstrap_demo_data=True,
        smtp_host=None,
    )
    app = create_app(settings)
    return TestClient(app)


def test_dashboard_and_alert_flow(tmp_path):
    client = create_test_client(tmp_path)

    dashboard = client.get("/api/dashboard")
    assert dashboard.status_code == 200
    data = dashboard.json()
    assert data["stats"]["total_devices"] == 3

    response = client.post(
        "/api/telemetry/vitals",
        json={
            "device_key": "patient-kit-01",
            "heart_rate_bpm": 144,
            "spo2_percent": 89,
            "body_temperature_c": 39.4,
            "systolic_bp": 182,
            "diastolic_bp": 122,
            "signal_quality": "good",
        },
    )
    assert response.status_code == 200
    assert response.json()["alerts_created"] >= 3

    alerts = client.get("/api/alerts?status=open")
    assert alerts.status_code == 200
    alert_items = alerts.json()
    assert alert_items
    assert any(item["severity"] == "critical" for item in alert_items)

    ack_response = client.post(f"/api/alerts/{alert_items[0]['id']}/acknowledge")
    assert ack_response.status_code == 200
    assert ack_response.json()["status"] == "acknowledged"


def test_register_device_and_store_medicine_box_event(tmp_path):
    client = create_test_client(tmp_path)

    register = client.post(
        "/api/devices/register",
        json={
            "device_key": "medbox-02",
            "name": "Secured Medicine Box 02",
            "type": "medicine_box",
            "patient_name": "Test Patient",
            "location_label": "Room 202",
            "metadata": {"source": "test"},
        },
    )
    assert register.status_code == 201

    event = client.post(
        "/api/telemetry/medicine-box",
        json={
            "device_key": "medbox-02",
            "uid": "UNAUTHORIZED",
            "authorized": False,
            "action": "unlock_attempt",
            "notes": "Unexpected scan",
        },
    )
    assert event.status_code == 200
    assert event.json()["alerts_created"] == 1

    recent = client.get("/api/telemetry/recent")
    assert recent.status_code == 200
    assert recent.json()[0]["category"] == "medicine_box"
