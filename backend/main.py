"""
Main FastAPI application
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.api import router as api_router
from app.websocket import router as websocket_router
from app.db.database import init_db

# Create FastAPI app
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="八十分在线纸牌游戏后端API"
)

@app.on_event("startup")
async def startup_event():
    # 初始化数据库
    await init_db()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(api_router, prefix="/api")
app.include_router(websocket_router, prefix="/ws")

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Quatre-Vingt Backend API",
        "version": settings.app_version,
        "status": "running"
    }

@app.api_route("/health", methods=["GET", "HEAD"])
async def health_check():
    """Health check endpoint - supports both GET and HEAD methods"""
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug
    )
