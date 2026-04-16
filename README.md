# IoT Patient Monitoring Platform

This repository is a professional, GitHub-ready implementation of the architecture described in the paper **"IoT Based Patient Monitoring System"**. It models the three major subsystems from the paper:

- Patient health monitoring for vital signs such as heart rate, SpO2, temperature, and blood pressure
- Ambient environment monitoring for room safety, air quality, and GPS location
- A secured medicine box with RFID/NFC-style access control and alerting

The project is intentionally structured as a realistic product foundation rather than a single prototype script. It includes:

- A FastAPI backend with typed REST endpoints
- Persistent telemetry, alert, device, and notification data
- A live monitoring dashboard
- Rule-based safety and clinical alerting
- Email and GSM/SMS notification adapters
- Device simulators so the system can be demonstrated without hardware
- Automated tests and supporting documentation

## Why this implementation

The paper describes an integrated IoT system, but several sections are still conceptual or marked "To be written". This codebase fills in those missing implementation layers with a practical software platform that maps cleanly onto the paper's design while staying easy to run and extend.

## Architecture

The platform uses three logical device classes:

1. `patient_monitor`: streams vitals such as heart rate, SpO2, body temperature, and blood pressure
2. `ambient_monitor`: streams room temperature, humidity, barometric pressure, fire/smoke status, and GPS coordinates
3. `medicine_box`: records RFID/NFC access attempts, inventory reminders, and tamper events

Incoming telemetry is stored in SQLite by default, evaluated against alert thresholds, broadcast to the live dashboard, and queued for notification delivery.

See [docs/architecture.md](docs/architecture.md) and [docs/paper-to-product.md](docs/paper-to-product.md) for the detailed mapping.

## Quick start

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e .[dev]
cp .env.example .env
uvicorn iot_monitoring.main:app --reload
```

Open `http://127.0.0.1:8000` for the dashboard and `http://127.0.0.1:8000/docs` for the API docs.

## Run the demo stream

With the API running in another terminal:

```bash
source .venv/bin/activate
python simulators/demo_stream.py
```

The simulator registers paper-inspired devices and continuously posts realistic telemetry, including occasional emergency events to exercise the alerting pipeline.

## Development commands

```bash
pytest
uvicorn iot_monitoring.main:app --reload
```

## Project layout

```text
iot-patient-monitoring-platform/
├── docs/
├── simulators/
├── src/iot_monitoring/
│   ├── routers/
│   ├── services/
│   ├── static/
│   └── templates/
└── tests/
```

## Suggested next steps for real hardware

- Replace the simulator with ESP32 firmware clients for each subsystem
- Connect the email adapter to an SMTP server and the GSM adapter to Twilio or a SIM800-style modem service
- Add authentication for device registration and clinician access
- Swap SQLite for PostgreSQL before multi-user deployment

## License

This project is provided as a reference implementation. Add your preferred open-source license before publishing publicly.
