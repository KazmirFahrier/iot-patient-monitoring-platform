# Architecture

## Overview

This project converts the original `EEE 416` course-project architecture into a working software platform with five layers:

1. Device layer
2. Ingestion API
3. Persistence and rule evaluation
4. Notification fan-out
5. Monitoring dashboard

## Device layer

The original prototype grouped the hardware into three subsystems. The software mirrors that grouping:

- `patient_monitor`: vital-sign device, intended for MAX30102, DS18B20, and blood-pressure data
- `ambient_monitor`: environmental device, intended for DHT11, BMP180, MQ2, flame, and GPS data
- `medicine_box`: secure access controller for RFID/NFC events

## Ingestion API

Each subsystem posts structured JSON to a dedicated endpoint:

- `POST /api/telemetry/vitals`
- `POST /api/telemetry/ambient`
- `POST /api/telemetry/medicine-box`

Devices are registered through `POST /api/devices/register`, which lets the dashboard and alerts display patient and location context.

## Persistence and alerting

Every telemetry submission becomes a `TelemetryRecord`. The same write path also evaluates threshold rules and generates `Alert` rows when necessary.

The current rule set includes:

- abnormal heart rate
- low oxygen saturation
- fever and high blood pressure
- smoke and flame detection
- medicine-box tamper or unauthorized access

## Notifications

Alerts are fanned out to:

- the dashboard feed
- email
- GSM/SMS

Email is live when SMTP settings are provided. GSM is implemented as a development stub so the repository stays runnable without vendor credentials.

## Dashboard

The web dashboard is served directly from FastAPI and subscribes to a WebSocket stream. Operators can see:

- device registration state
- recent telemetry
- open alerts
- compact trend charts for key metrics

## Deployment model

The default profile uses SQLite for easy local demos and GitHub publication. For production, swap to PostgreSQL, add authentication, and run the service behind a reverse proxy.
