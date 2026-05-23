"""
HezGene Web — WebSocket connection manager for live evolution streaming.
"""

from __future__ import annotations

from fastapi import WebSocket


class ConnectionManager:
    """Manages WebSocket connections for live evolution streaming."""

    def __init__(self):
        self._connections: dict[str, WebSocket] = {}

    async def connect(self, session_id: str, websocket: WebSocket):
        await websocket.accept()
        self._connections[session_id] = websocket

    def disconnect(self, session_id: str):
        if session_id in self._connections:
            del self._connections[session_id]

    async def send(self, session_id: str, data: dict):
        """Send JSON data to a specific session's WebSocket."""
        if session_id in self._connections:
            try:
                await self._connections[session_id].send_json(data)
            except Exception:
                self.disconnect(session_id)

    async def broadcast(self, data: dict):
        """Send to all connected clients."""
        disconnected = []
        for sid, ws in self._connections.items():
            try:
                await ws.send_json(data)
            except Exception:
                disconnected.append(sid)
        for sid in disconnected:
            self.disconnect(sid)

    def is_connected(self, session_id: str) -> bool:
        return session_id in self._connections


manager = ConnectionManager()
