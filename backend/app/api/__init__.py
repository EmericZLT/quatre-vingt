"""
API routes
"""
from fastapi import APIRouter
from .game import router as game_router

router = APIRouter()

# Include sub-routers
router.include_router(game_router, prefix="/game", tags=["game"])