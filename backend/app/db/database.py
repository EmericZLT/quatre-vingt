from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base
import os

# 数据库文件路径
DB_FILE = "game.db"
DATABASE_URL = f"sqlite+aiosqlite:///./{DB_FILE}"

# 创建异步引擎
engine = create_async_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},  # SQLite 异步需要
)

# 创建异步 Session 工厂
async_session = sessionmaker(
    engine, 
    class_=AsyncSession, 
    expire_on_commit=False
)

# 声明式基类
Base = declarative_base()

# 获取数据库 Session 的依赖
async def get_db():
    async with async_session() as session:
        yield session

# 初始化数据库（创建表）
async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

