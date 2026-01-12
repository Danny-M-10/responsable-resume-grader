"""
WebSocket endpoint for real-time progress updates
"""
from fastapi import WebSocket, WebSocketDisconnect
import json
import logging
from typing import Dict, Set

logger = logging.getLogger(__name__)

# #region agent log
def _log_debug(hypothesis_id, location, message, data=None):
    """Log debug info to CloudWatch via standard logger"""
    try:
        import json
        data_str = json.dumps(data or {}) if data else "{}"
        logger.info(f"[HYP-{hypothesis_id}] {location}: {message} | {data_str}")
    except Exception as e:
        logger.error(f"Failed to log debug info: {e}")
# #endregion agent log

# Store active WebSocket connections
active_connections: Dict[str, Set[WebSocket]] = {}


async def websocket_endpoint(websocket: WebSocket, client_id: str = "default"):
    """
    WebSocket endpoint for progress updates
    
    Args:
        websocket: WebSocket connection
        client_id: Client identifier for grouping connections (default: "default")
    """
    await websocket.accept()
    # #region agent log
    _log_debug("B", "progress.py:30", "WebSocket accepted", {"client_id": client_id})
    # #endregion agent log
    
    if client_id not in active_connections:
        active_connections[client_id] = set()
    
    active_connections[client_id].add(websocket)
    # #region agent log
    _log_debug("B", "progress.py:36", "WebSocket added to active connections", {"client_id": client_id, "total_connections": len(active_connections[client_id])})
    # #endregion agent log
    logger.info(f"WebSocket connected: {client_id}, total connections: {len(active_connections[client_id])}")
    
    try:
        while True:
            # Keep connection alive and handle any incoming messages
            data = await websocket.receive_text()
            # Echo back or handle client messages if needed
            await websocket.send_text(json.dumps({"type": "pong", "message": "Connection alive"}))
    except WebSocketDisconnect:
        # #region agent log
        _log_debug("B", "progress.py:45", "WebSocket disconnected", {"client_id": client_id})
        # #endregion agent log
        if client_id in active_connections:
            active_connections[client_id].discard(websocket)
            logger.info(f"WebSocket disconnected: {client_id}, remaining connections: {len(active_connections.get(client_id, set()))}")
            if not active_connections[client_id]:
                del active_connections[client_id]
    except Exception as e:
        # #region agent log
        _log_debug("B", "progress.py:52", "WebSocket error", {"client_id": client_id, "error": str(e)})
        # #endregion agent log
        logger.error(f"WebSocket error: {e}")
        if client_id in active_connections:
            active_connections[client_id].discard(websocket)
            if not active_connections[client_id]:
                del active_connections[client_id]


async def send_progress_update(client_id: str, step: str, progress: float, current: int = None, total: int = None, message: str = None):
    """
    Send progress update to all connections for a given client_id
    
    Args:
        client_id: Client identifier
        step: Current step name
        progress: Progress value (0.0 to 1.0)
        current: Current item number
        total: Total items
        message: Optional message
    """
    # #region agent log
    _log_debug("B", "progress.py:58", "send_progress_update called", {"client_id": client_id, "step": step, "progress": progress, "has_connections": client_id in active_connections, "connection_count": len(active_connections.get(client_id, set()))})
    # #endregion agent log
    if client_id not in active_connections:
        # #region agent log
        _log_debug("B", "progress.py:64", "No active connections for client_id", {"client_id": client_id})
        # #endregion agent log
        return
    
    update = {
        "type": "progress",
        "step": step,
        "progress": progress,
        "current": current,
        "total": total,
        "message": message
    }
    
    message_text = json.dumps(update)
    disconnected = set()
    
    for connection in active_connections[client_id]:
        try:
            await connection.send_text(message_text)
            # #region agent log
            _log_debug("B", "progress.py:81", "Progress update sent successfully", {"client_id": client_id, "step": step})
            # #endregion agent log
        except Exception as e:
            # #region agent log
            _log_debug("B", "progress.py:85", "Failed to send progress update", {"client_id": client_id, "error": str(e)})
            # #endregion agent log
            logger.error(f"Failed to send progress update: {e}")
            disconnected.add(connection)
    
    # Remove disconnected connections
    for conn in disconnected:
        active_connections[client_id].discard(conn)
    
    if not active_connections[client_id]:
        del active_connections[client_id]

