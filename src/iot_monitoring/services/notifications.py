from __future__ import annotations

import smtplib
from email.message import EmailMessage

from sqlalchemy.orm import Session

from iot_monitoring.config import Settings
from iot_monitoring.models import Alert, NotificationDispatch


class NotificationService:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def dispatch_for_alert(self, session: Session, alert: Alert) -> list[NotificationDispatch]:
        dispatches = [
            self._send_email(session, alert),
            self._send_gsm(session, alert),
        ]
        return dispatches

    def _send_email(self, session: Session, alert: Alert) -> NotificationDispatch:
        recipient = self.settings.alert_email_to

        if not self.settings.smtp_host:
            dispatch = NotificationDispatch(
                alert=alert,
                channel="email",
                recipient=recipient,
                status="skipped",
                response="SMTP is not configured; recorded as a demo notification.",
            )
            session.add(dispatch)
            return dispatch

        message = EmailMessage()
        message["From"] = self.settings.smtp_from
        message["To"] = recipient
        message["Subject"] = f"[{alert.severity.value.upper()}] {alert.title}"
        message.set_content(alert.message)

        try:
            with smtplib.SMTP(self.settings.smtp_host, self.settings.smtp_port, timeout=10) as smtp:
                smtp.starttls()
                if self.settings.smtp_username and self.settings.smtp_password:
                    smtp.login(self.settings.smtp_username, self.settings.smtp_password)
                smtp.send_message(message)
            status = "sent"
            response = "Delivered over SMTP."
        except Exception as exc:
            status = "failed"
            response = str(exc)

        dispatch = NotificationDispatch(
            alert=alert,
            channel="email",
            recipient=recipient,
            status=status,
            response=response,
        )
        session.add(dispatch)
        return dispatch

    def _send_gsm(self, session: Session, alert: Alert) -> NotificationDispatch:
        response = (
            "GSM adapter is stubbed for development. "
            f"Queued SMS content: {alert.title} - {alert.message}"
        )
        dispatch = NotificationDispatch(
            alert=alert,
            channel="gsm",
            recipient=self.settings.gsm_recipient,
            status="queued",
            response=response,
        )
        session.add(dispatch)
        return dispatch
