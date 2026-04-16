from __future__ import annotations

from dataclasses import dataclass

from iot_monitoring.models import AlertSeverity


@dataclass(slots=True)
class RuleHit:
    severity: AlertSeverity
    title: str
    message: str
    channels: list[str]
    context: dict


def evaluate_vitals(payload: dict, device_name: str, patient_name: str | None) -> list[RuleHit]:
    patient_label = patient_name or "Unknown patient"
    findings: list[RuleHit] = []
    hr = payload["heart_rate_bpm"]
    spo2 = payload["spo2_percent"]
    temp = payload["body_temperature_c"]
    systolic = payload.get("systolic_bp")
    diastolic = payload.get("diastolic_bp")

    if hr < 40 or hr > 130:
        findings.append(
            RuleHit(
                severity=AlertSeverity.critical,
                title="Critical heart-rate reading",
                message=f"{patient_label} on {device_name} recorded {hr:.0f} bpm.",
                channels=["dashboard", "email", "gsm"],
                context={"metric": "heart_rate_bpm", "value": hr},
            )
        )
    elif hr < 50 or hr > 120:
        findings.append(
            RuleHit(
                severity=AlertSeverity.warning,
                title="Heart-rate warning",
                message=f"{patient_label} on {device_name} recorded {hr:.0f} bpm.",
                channels=["dashboard", "email"],
                context={"metric": "heart_rate_bpm", "value": hr},
            )
        )

    if spo2 < 92:
        findings.append(
            RuleHit(
                severity=AlertSeverity.critical,
                title="Critical oxygen saturation",
                message=f"{patient_label} on {device_name} recorded SpO2 at {spo2:.1f}%.",
                channels=["dashboard", "email", "gsm"],
                context={"metric": "spo2_percent", "value": spo2},
            )
        )
    elif spo2 < 95:
        findings.append(
            RuleHit(
                severity=AlertSeverity.warning,
                title="Low oxygen saturation",
                message=f"{patient_label} on {device_name} recorded SpO2 at {spo2:.1f}%.",
                channels=["dashboard", "email"],
                context={"metric": "spo2_percent", "value": spo2},
            )
        )

    if temp >= 39:
        findings.append(
            RuleHit(
                severity=AlertSeverity.critical,
                title="Critical body temperature",
                message=f"{patient_label} on {device_name} recorded {temp:.1f} C body temperature.",
                channels=["dashboard", "email", "gsm"],
                context={"metric": "body_temperature_c", "value": temp},
            )
        )
    elif temp >= 38:
        findings.append(
            RuleHit(
                severity=AlertSeverity.warning,
                title="Elevated body temperature",
                message=f"{patient_label} on {device_name} recorded {temp:.1f} C body temperature.",
                channels=["dashboard", "email"],
                context={"metric": "body_temperature_c", "value": temp},
            )
        )

    if systolic and diastolic:
        if systolic >= 180 or diastolic >= 120:
            findings.append(
                RuleHit(
                    severity=AlertSeverity.critical,
                    title="Critical blood pressure",
                    message=(
                        f"{patient_label} on {device_name} recorded blood pressure "
                        f"{systolic}/{diastolic} mmHg."
                    ),
                    channels=["dashboard", "email", "gsm"],
                    context={"metric": "blood_pressure", "value": f"{systolic}/{diastolic}"},
                )
            )
        elif systolic >= 140 or diastolic >= 90:
            findings.append(
                RuleHit(
                    severity=AlertSeverity.warning,
                    title="Blood pressure warning",
                    message=(
                        f"{patient_label} on {device_name} recorded blood pressure "
                        f"{systolic}/{diastolic} mmHg."
                    ),
                    channels=["dashboard", "email"],
                    context={"metric": "blood_pressure", "value": f"{systolic}/{diastolic}"},
                )
            )

    return findings


def evaluate_ambient(payload: dict, device_name: str, patient_name: str | None) -> list[RuleHit]:
    patient_label = patient_name or "Unknown patient"
    findings: list[RuleHit] = []

    if payload.get("smoke_detected"):
        findings.append(
            RuleHit(
                severity=AlertSeverity.critical,
                title="Smoke detected",
                message=f"Smoke was detected near {patient_label} by {device_name}.",
                channels=["dashboard", "email", "gsm"],
                context={"metric": "smoke_detected", "value": True},
            )
        )

    if payload.get("flame_detected"):
        findings.append(
            RuleHit(
                severity=AlertSeverity.critical,
                title="Flame detected",
                message=f"Flame was detected near {patient_label} by {device_name}.",
                channels=["dashboard", "email", "gsm"],
                context={"metric": "flame_detected", "value": True},
            )
        )

    room_temp = payload["room_temperature_c"]
    if room_temp >= 35:
        findings.append(
            RuleHit(
                severity=AlertSeverity.warning,
                title="High room temperature",
                message=f"{device_name} measured room temperature at {room_temp:.1f} C.",
                channels=["dashboard", "email"],
                context={"metric": "room_temperature_c", "value": room_temp},
            )
        )

    return findings


def evaluate_medicine_box(payload: dict, device_name: str, patient_name: str | None) -> list[RuleHit]:
    patient_label = patient_name or "Unknown patient"
    findings: list[RuleHit] = []
    action = payload["action"]

    if action == "forced_open":
        findings.append(
            RuleHit(
                severity=AlertSeverity.critical,
                title="Medicine box tamper event",
                message=f"{device_name} detected a forced-open event for {patient_label}.",
                channels=["dashboard", "email", "gsm"],
                context={"metric": "forced_open", "value": True, "uid": payload["uid"]},
            )
        )
    elif not payload["authorized"]:
        findings.append(
            RuleHit(
                severity=AlertSeverity.critical,
                title="Unauthorized medicine-box access",
                message=(
                    f"{device_name} rejected RFID/NFC UID {payload['uid']} for {patient_label}."
                ),
                channels=["dashboard", "email", "gsm"],
                context={"metric": "authorized", "value": False, "uid": payload["uid"]},
            )
        )
    elif action == "inventory_reminder":
        findings.append(
            RuleHit(
                severity=AlertSeverity.info,
                title="Medicine refill reminder",
                message=f"{device_name} raised a refill reminder for {patient_label}.",
                channels=["dashboard", "email"],
                context={"metric": "inventory", "value": "low"},
            )
        )

    return findings
