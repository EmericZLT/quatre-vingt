from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import delete
from app.db.database import get_db
from app.models.user import User, Stats
from app.core.security import get_password_hash, verify_password, create_access_token, get_current_user_optional
from pydantic import BaseModel, Field
from datetime import datetime, timedelta

router = APIRouter()

# --- 请求与响应模型 ---

class UserRegister(BaseModel):
    username: str = Field(..., min_length=2, max_length=15)
    password: str = Field(..., min_length=6)

class UserLogin(BaseModel):
    username: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    username: str
    is_admin: bool

# --- API 接口 ---

@router.post("/register", response_model=Token)
async def register(user_in: UserRegister, db: AsyncSession = Depends(get_db)):
    """用户注册"""
    # 检查用户是否已存在
    result = await db.execute(select(User).where(User.username == user_in.username))
    if result.scalars().first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="用户名已被占用"
        )
    
    # 创建新用户
    hashed_password = get_password_hash(user_in.password)
    # 第一个注册的用户设为管理员（简单演示用）
    user_count_result = await db.execute(select(User))
    is_admin = user_count_result.scalars().first() is None
    
    new_user = User(
        username=user_in.username,
        password_hash=hashed_password,
        is_admin=is_admin
    )
    db.add(new_user)
    await db.flush()  # 获取用户 ID
    
    # 初始化战绩表
    new_stats = Stats(user_id=new_user.id)
    db.add(new_stats)
    
    await db.commit()
    await db.refresh(new_user)
    
    access_token = create_access_token(data={"sub": new_user.username})
    return {
        "access_token": access_token, 
        "token_type": "bearer", 
        "username": new_user.username,
        "is_admin": new_user.is_admin
    }

@router.post("/login", response_model=Token)
async def login(user_in: UserLogin, db: AsyncSession = Depends(get_db)):
    """用户登录"""
    result = await db.execute(select(User).where(User.username == user_in.username))
    user = result.scalars().first()
    
    if not user or not verify_password(user_in.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误"
        )
    
    # 更新活跃时间
    from datetime import datetime
    user.last_active = datetime.utcnow()
    await db.commit()
    
    access_token = create_access_token(data={"sub": user.username})
    return {
        "access_token": access_token, 
        "token_type": "bearer", 
        "username": user.username,
        "is_admin": user.is_admin
    }

@router.delete("/cleanup")
async def cleanup_inactive_users(
    days: int = 30,
    username: str = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_db)
):
    """
    管理员清理不活跃用户
    days: 清理多少天未登录的用户，默认30天
    """
    if not username:
        raise HTTPException(status_code=401, detail="未登录")
    
    # 检查是否为管理员
    result = await db.execute(select(User).where(User.username == username))
    admin_user = result.scalars().first()
    if not admin_user or not admin_user.is_admin:
        raise HTTPException(status_code=403, detail="没有管理员权限")
    
    cutoff_date = datetime.utcnow() - timedelta(days=days)
    
    # 查找不活跃且非管理员的用户
    inactive_query = select(User).where(
        User.last_active < cutoff_date,
        User.is_admin == False
    )
    result = await db.execute(inactive_query)
    users_to_delete = result.scalars().all()
    user_ids = [u.id for u in users_to_delete]
    
    if not user_ids:
        return {"message": "没有找到需要清理的用户", "deleted_count": 0}
    
    # 删除对应的统计数据
    await db.execute(delete(Stats).where(Stats.user_id.in_(user_ids)))
    # 删除用户
    await db.execute(delete(User).where(User.id.in_(user_ids)))
    
    await db.commit()
    
    return {
        "message": f"成功清理了 {len(user_ids)} 个 {days} 天未登录的用户",
        "deleted_count": len(user_ids)
    }

