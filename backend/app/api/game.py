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
    room_id = str(uuid.uuid4())
    room = GameRoom(id=room_id, name=request.name)
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
    
    room = rooms[room_id]
    
    # 检查玩家是否已经在房间中
    existing_player = next((p for p in room.players if p.name == request.player_name), None)
    if existing_player:
        return room
    
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
        name=request.player_name,
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
