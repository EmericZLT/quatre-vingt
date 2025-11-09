"""
API routes
"""
from fastapi import APIRouter
from .game import router as game_router

router = APIRouter()

# Include sub-routers
# game_router 已经包含了 /rooms 等路由，直接包含即可
router.include_router(game_router, tags=["game"])