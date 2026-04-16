from __future__ import annotations

from pathlib import Path

from dataclasses import dataclass

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from iot_monitoring.config import Settings
from iot_monitoring.database import Base, create_session_factory, create_sqlalchemy_engine
from iot_monitoring.routers import alerts, dashboard, devices, telemetry
from iot_monitoring.services.bootstrap import seed_demo_devices
from iot_monitoring.services.notifications import NotificationService
from iot_monitoring.services.realtime import RealtimeManager


@dataclass(slots=True)
class AppContext:
    settings: Settings
    engine: object
    session_factory: object
    notifier: NotificationService
    realtime: RealtimeManager


def create_app(settings: Settings | None = None) -> FastAPI:
    resolved_settings = settings or Settings()
    engine = create_sqlalchemy_engine(resolved_settings.database_url)
    session_factory = create_session_factory(engine)
    notifier = NotificationService(resolved_settings)
    realtime = RealtimeManager()

    package_root = Path(__file__).parent

    app = FastAPI(
        title=resolved_settings.app_name,
        version="0.1.0",
        description="Reference implementation of an IoT-based patient monitoring platform.",
    )
    app.state.context = AppContext(
        settings=resolved_settings,
        engine=engine,
        session_factory=session_factory,
        notifier=notifier,
        realtime=realtime,
    )

    Base.metadata.create_all(bind=engine)
    if resolved_settings.bootstrap_demo_data:
        with session_factory() as session:
            seed_demo_devices(session)

    app.mount("/static", StaticFiles(directory=package_root / "static"), name="static")
    app.include_router(dashboard.router)
    app.include_router(devices.router, prefix="/api")
    app.include_router(telemetry.router, prefix="/api")
    app.include_router(alerts.router, prefix="/api")

    return app
