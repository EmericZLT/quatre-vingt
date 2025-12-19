"""
API routes
"""
from fastapi import APIRouter
from .game import router as game_router
from .auth import router as auth_router

router = APIRouter()

# Include sub-routers
router.include_router(game_router, tags=["game"])
router.include_router(auth_router, prefix="/auth", tags=["auth"])