"""WebSocket endpoint for real-time analysis progress."""

import asyncio
import json

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from sqlalchemy import select

from core.logging import get_logger
from infrastructure.database.orm_models import RepositoryORM
from infrastructure.database.postgres import get_session

router = APIRouter(tags=["Progress"])
logger = get_logger(__name__)

POLL_INTERVAL = 1.5  # seconds between DB checks
TERMINAL_STATUSES = {"complete", "failed"}


@router.websocket("/ws/progress/{repo_id}")
async def repo_progress(websocket: WebSocket, repo_id: str) -> None:
    """Stream repository analysis status updates to the client."""
    await websocket.accept()
    logger.info("WebSocket opened", repo_id=repo_id)

    try:
        while True:
            async with get_session() as session:
                row = await session.get(RepositoryORM, repo_id)

            if not row:
                await websocket.send_text(
                    json.dumps({"status": "not_found", "repo_id": repo_id})
                )
                await websocket.close(code=1008)
                return

            payload = {
                "repo_id": repo_id,
                "status": row.status,
                "file_count": row.file_count,
                "total_lines": row.total_lines,
                "error_message": row.error_message,
            }
            await websocket.send_text(json.dumps(payload))

            if row.status in TERMINAL_STATUSES:
                await asyncio.sleep(0.5)
                await websocket.close()
                return

            await asyncio.sleep(POLL_INTERVAL)

    except WebSocketDisconnect:
        logger.info("WebSocket disconnected", repo_id=repo_id)
    except Exception as exc:
        logger.error("WebSocket error", repo_id=repo_id, error=str(exc))
        await websocket.close(code=1011)
