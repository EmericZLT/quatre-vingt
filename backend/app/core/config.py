"""
Application configuration settings
"""
from pydantic_settings import BaseSettings
from typing import Optional, List
import json
import os


class Settings(BaseSettings):
    """Application settings"""
    
    # Application
    app_name: str = "Quatre-Vingt Backend"
    app_version: str = "1.0.0"
    debug: bool = False
    
    # Server
    host: str = "0.0.0.0"
    port: int = 8000
    
    # Database
    database_url: Optional[str] = None
    redis_url: str = "redis://localhost:6379"
    
    # Security
    secret_key: str = "your-secret-key-here"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    
    # CORS - 默认值，会从环境变量覆盖
    allowed_origins: List[str] = [
        "http://localhost:3000",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:4173",
        "http://127.0.0.1:4173",
    ]
    
    # Game settings
    max_players_per_room: int = 4
    game_timeout_minutes: int = 60
    
    class Config:
        env_file = ".env"
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # 从环境变量读取 CORS 配置（支持 JSON 数组格式或逗号分隔）
        cors_env = os.getenv("ALLOWED_ORIGINS") or os.getenv("CORS_ORIGINS")
        if cors_env:
            try:
                # 尝试解析为 JSON 数组
                parsed = json.loads(cors_env)
                if isinstance(parsed, list):
                    self.allowed_origins = parsed
            except (json.JSONDecodeError, TypeError):
                # 如果不是 JSON，按逗号分割
                self.allowed_origins = [origin.strip() for origin in cors_env.split(",") if origin.strip()]


settings = Settings()
