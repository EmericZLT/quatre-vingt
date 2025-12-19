"""
Game API endpoints
"""
from fastapi import APIRouter, HTTPException
from typing import List
from pydantic import BaseModel
import uuid
from app.models.game import GameRoom, Player, PlayerPosition

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
async def create_room(request: CreateRoomRequest) -> GameRoom:
    """Create a new game room"""
    # 验证房间名长度
    room_name = request.name.strip()
    if not room_name:
        raise HTTPException(status_code=400, detail="房间名不能为空")
    if len(room_name) > 15:
        raise HTTPException(status_code=400, detail="房间名不能超过15个字符")
    
    # 验证出牌时间限制
    play_time_limit = request.play_time_limit
    if play_time_limit not in [0, 10, 18, 25]:
        raise HTTPException(status_code=400, detail="出牌时间限制必须为0（不限制）、10、18或25秒")
    
    # 验证升级模式
    level_up_mode = request.level_up_mode
    if level_up_mode not in ["default", "standard"]:
        raise HTTPException(status_code=400, detail="升级模式必须为default（滁州版）或standard（国标版）")
    
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

@router.get("/rooms/{room_id}")
async def get_room(room_id: str) -> GameRoom:
    """Get a specific game room"""
    if room_id not in rooms:
        raise HTTPException(status_code=404, detail="Room not found")
    return rooms[room_id]

@router.post("/rooms/{room_id}/join")
async def join_room(room_id: str, request: JoinRoomRequest) -> GameRoom:
    """Join a game room"""
    if room_id not in rooms:
        raise HTTPException(status_code=404, detail="Room not found")
    
    # 验证玩家名长度
    player_name = request.player_name.strip()
    if not player_name:
        raise HTTPException(status_code=400, detail="玩家名不能为空")
    if len(player_name) > 8:
        raise HTTPException(status_code=400, detail="玩家名不能超过8个字符")
    
    room = rooms[room_id]
    
    # 检查玩家是否已经在房间中（用于重连）
    existing_player = next((p for p in room.players if p.name == player_name), None)
    if existing_player:
        return room
    
    # 检查房间中是否已有同名玩家（不允许重名）
    if any(p.name == player_name for p in room.players):
        raise HTTPException(status_code=400, detail="该名称已被使用，请选择其他名称")
    
    if room.is_full:
        raise HTTPException(status_code=400, detail="Room is full")
    
    # Assign position based on current players (逆时针顺序：北-西-南-东)
    positions = [PlayerPosition.NORTH, PlayerPosition.WEST, PlayerPosition.SOUTH, PlayerPosition.EAST]
    used_positions = {player.position for player in room.players}
    available_positions = [pos for pos in positions if pos not in used_positions]
    
    if not available_positions:
        raise HTTPException(status_code=400, detail="No available positions")
    
    player = Player(
        id=str(uuid.uuid4()),
        name=player_name,
        position=available_positions[0]
    )
    # 默认准备就绪
    player.is_ready = True
    # 生成用于重连的token
    player.token = str(uuid.uuid4())
    
    room.players.append(player)
    # 如果是第一个玩家，设为房主
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
