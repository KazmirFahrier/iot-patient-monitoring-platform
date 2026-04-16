from __future__ import annotations

import json
from collections.abc import Iterable

from fastapi import WebSocket


class RealtimeManager:
    def __init__(self) -> None:
        self._connections: set[WebSocket] = set()

    async def connect(self, websocket: WebSocket) -> None:
        await websocket.accept()
        self._connections.add(websocket)

    def disconnect(self, websocket: WebSocket) -> None:
        self._connections.discard(websocket)

    async def broadcast(self, event: str, payload: dict) -> None:
        dead_connections: list[WebSocket] = []
        message = json.dumps({"event": event, "payload": payload}, default=str)
        for connection in self._iter_connections():
            try:
                await connection.send_text(message)
            except Exception:
                dead_connections.append(connection)

        for websocket in dead_connections:
            self.disconnect(websocket)

    def _iter_connections(self) -> Iterable[WebSocket]:
        return tuple(self._connections)
