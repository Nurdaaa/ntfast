"""
WebSocket Manager for Analysis Progress
Менеджер реал-тайм прогресса анализа через WebSocket
"""
import asyncio
import logging
from typing import Dict, Set, Optional, Callable
from datetime import datetime

from fastapi import WebSocket

logger = logging.getLogger(__name__)


class AnalysisProgressManager:
    """
    Управляет WebSocket-подключениями для прогресса анализа.

    Клиент подключается к /ws/analysis/{session_id} и получает
    обновления прогресса в реальном времени.

    Сообщения:
        { type: "progress", step, percent, message, detail }
        { type: "completed", percent: 100 }
        { type: "error", message }
    """

    def __init__(self):
        # session_id → Set[WebSocket]
        self._connections: Dict[str, Set[WebSocket]] = {}
        # session_id → last progress state
        self._progress_state: Dict[str, dict] = {}

    async def connect(self, websocket: WebSocket, session_id: str):
        """Подключить клиента к каналу прогресса."""
        await websocket.accept()
        if session_id not in self._connections:
            self._connections[session_id] = set()
        self._connections[session_id].add(websocket)
        logger.info(f"WS Analysis connected: session={session_id}")

        # Если есть текущий прогресс — отправить его сразу
        if session_id in self._progress_state:
            try:
                await websocket.send_json(self._progress_state[session_id])
            except Exception:
                pass

    def disconnect(self, websocket: WebSocket, session_id: str):
        """Отключить клиента."""
        if session_id in self._connections:
            self._connections[session_id].discard(websocket)
            if not self._connections[session_id]:
                del self._connections[session_id]
        logger.info(f"WS Analysis disconnected: session={session_id}")

    async def send_progress(self, session_id: str, step: str, percent: int,
                            message: str, detail: str = ""):
        """Отправить обновление прогресса всем слушателям сессии."""
        payload = {
            "type": "progress",
            "step": step,
            "percent": min(percent, 100),
            "message": message,
            "detail": detail,
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
        self._progress_state[session_id] = payload
        await self._broadcast_to_session(session_id, payload)

    async def send_completed(self, session_id: str):
        """Отправить уведомление о завершении."""
        payload = {
            "type": "completed",
            "percent": 100,
            "message": "Анализ завершён",
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
        self._progress_state[session_id] = payload
        await self._broadcast_to_session(session_id, payload)
        # Очистить состояние через 30 секунд
        asyncio.get_event_loop().call_later(30, self._cleanup_session, session_id)

    async def send_error(self, session_id: str, message: str):
        """Отправить уведомление об ошибке."""
        payload = {
            "type": "error",
            "message": message,
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
        self._progress_state[session_id] = payload
        await self._broadcast_to_session(session_id, payload)

    async def _broadcast_to_session(self, session_id: str, payload: dict):
        """Отправить сообщение всем подключённым к сессии."""
        if session_id not in self._connections:
            return

        disconnected = set()
        for ws in self._connections[session_id]:
            try:
                await ws.send_json(payload)
            except Exception:
                disconnected.add(ws)

        for ws in disconnected:
            self._connections[session_id].discard(ws)

    def _cleanup_session(self, session_id: str):
        """Очистить данные сессии."""
        self._progress_state.pop(session_id, None)

    def create_sync_callback(self, session_id: str, loop: asyncio.AbstractEventLoop):
        """
        Создать синхронный callback для вызова из analyze()
        (BankAnalyzer.analyze() — синхронный код).
        """
        def callback(step: str, percent: int, message: str, detail: str = ""):
            try:
                asyncio.run_coroutine_threadsafe(
                    self.send_progress(session_id, step, percent, message, detail),
                    loop
                )
            except Exception as e:
                logger.debug(f"Progress callback error: {e}")

        return callback


# Глобальный singleton
analysis_progress = AnalysisProgressManager()
