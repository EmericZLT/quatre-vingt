"""
Game API endpoints
"""
from fastapi import APIRouter, HTTPException, Depends
from typing import List, Optional
from pydantic import BaseModel
import uuid
from app.models.game import GameRoom, Player, PlayerPosition
from app.core.security import get_current_user_optional
from app.db.database import get_db
from app.models.user import User
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

router = APIRouter()

class CreateRoomRequest(BaseModel):
    name: str
    play_time_limit: int = 18  # 出牌等待时间（秒），默认18秒
    level_up_mode: str = "default"  # 升级模式："default"（滁州版）或"standard"（国标版）
    ace_reset_enabled: bool = True  # 连续3次打A不过是否重置级别，默认开启

class JoinRoomRequest(BaseModel):
    player_name: str

class ReconnectRequest(BaseModel):
    token: str

# In-memory storage for demo (will be replaced with database)
rooms: dict[str, GameRoom] = {}

@router.get("/rooms")
async def get_rooms() -> List[GameRoom]:
    """Get all game rooms"""
    return [room for room in rooms.values() if room.id != "demo"]

@router.post("/rooms")
async def create_room(
    request: CreateRoomRequest, 
    username: Optional[str] = Depends(get_current_user_optional)
) -> GameRoom:
    """Create a new game room"""
    # ... (原有验证逻辑保持不变)
    room_name = request.name.strip()
    if not room_name:
        raise HTTPException(status_code=400, detail="房间名不能为空")
    
    play_time_limit = request.play_time_limit
    level_up_mode = request.level_up_mode
    
    room_id = str(uuid.uuid4())
    room = GameRoom(
        id=room_id,
        name=room_name,
        play_time_limit=play_time_limit,
        level_up_mode=level_up_mode,
        ace_reset_enabled=request.ace_reset_enabled
    )
    rooms[room_id] = room
    return room

@router.post("/rooms/{room_id}/join")
async def join_room(
    room_id: str, 
    request: JoinRoomRequest,
    username: Optional[str] = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_db)
) -> GameRoom:
    """Join a game room"""
    if room_id not in rooms:
        raise HTTPException(status_code=404, detail="Room not found")
    
    room = rooms[room_id]
    player_name = request.player_name.strip()
    
    # 识别已登录用户
    user_id = None
    if username:
        result = await db.execute(select(User).where(User.username == username))
        user = result.scalars().first()
        if user:
            user_id = user.id
            player_name = user.username  # 登录用户强制使用用户名
    
    if not player_name:
        raise HTTPException(status_code=400, detail="玩家名不能为空")
    
    # 检查是否重复加入
    existing_player = None
    if user_id:
        existing_player = next((p for p in room.players if p.id == user_id), None)
    else:
        existing_player = next((p for p in room.players if p.name == player_name), None)
        
    if existing_player:
        return room
    
    if any(p.name == player_name for p in room.players):
        raise HTTPException(status_code=400, detail="该名称已被使用，请选择其他名称")
    
    if room.is_full:
        raise HTTPException(status_code=400, detail="Room is full")
    
    # 分配位置
    positions = [PlayerPosition.NORTH, PlayerPosition.WEST, PlayerPosition.SOUTH, PlayerPosition.EAST]
    used_positions = {player.position for player in room.players}
    available_positions = [pos for pos in positions if pos not in used_positions]
    
    if not available_positions:
        raise HTTPException(status_code=400, detail="No available positions")
    
    player = Player(
        id=user_id if user_id else str(uuid.uuid4()),
        name=player_name,
        position=available_positions[0],
        is_ready=True,
        token=str(uuid.uuid4())
    )
    
    room.players.append(player)
    if room.owner_id is None:
        room.owner_id = player.id

    return room

@router.post("/rooms/{room_id}/reconnect")
async def reconnect(room_id: str, request: ReconnectRequest) -> GameRoom:
    """Reconnect to a room using token"""
    if room_id not in rooms:
        raise HTTPException(status_code=404, detail="Room not found")
    room = rooms[room_id]
    player = next((p for p in room.players if p.token == request.token), None)
    if not player:
        raise HTTPException(status_code=401, detail="Invalid token")
    return room
