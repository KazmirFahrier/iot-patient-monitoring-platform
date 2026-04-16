from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, Depends, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from iot_monitoring.dependencies import get_session
from iot_monitoring.services.dashboard import build_dashboard_snapshot

router = APIRouter(tags=["dashboard"])
templates = Jinja2Templates(directory=str(Path(__file__).resolve().parent.parent / "templates"))


@router.get("/", response_class=HTMLResponse)
def dashboard_page(request: Request):
    return templates.TemplateResponse(
        "dashboard.html",
        {
            "request": request,
            "page_title": "IoT Patient Monitoring Platform",
        },
    )


@router.get("/api/dashboard")
def dashboard_snapshot(session: Session = Depends(get_session)):
    return build_dashboard_snapshot(session)


@router.websocket("/ws/live")
async def live_dashboard_socket(websocket: WebSocket):
    manager = websocket.app.state.context.realtime
    await manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)
