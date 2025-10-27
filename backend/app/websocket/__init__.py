"""
WebSocket routes
"""
from fastapi import APIRouter
from .game_websocket import router as game_websocket_router

router = APIRouter()

# Include WebSocket routers
router.include_router(game_websocket_router, prefix="/game", tags=["websocket"])