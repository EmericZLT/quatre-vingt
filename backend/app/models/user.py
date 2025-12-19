from sqlalchemy import Column, String, Integer, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
from app.db.database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    username = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    is_admin = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_active = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 关联战绩表 (一对一)
    stats = relationship("Stats", back_populates="user", uselist=False, cascade="all, delete-orphan")

class Stats(Base):
    __tablename__ = "user_stats"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String, ForeignKey("users.id"), unique=True)
    
    games_played = Column(Integer, default=0)
    wins = Column(Integer, default=0)
    
    # 累计升级数（仅统计正向增长）
    dealer_level_ups = Column(Integer, default=0)  # 作为庄家方的累计升级数
    idle_level_ups = Column(Integer, default=0)    # 作为闲家方的累计升级数
    
    total_score = Column(Integer, default=0)       # 生涯累计抓分总数

    user = relationship("User", back_populates="stats")

