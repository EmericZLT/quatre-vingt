"""
Game API endpoints
"""
from fastapi import APIRouter, HTTPException
from typing import List
from pydantic import BaseModel
from app.models.game import GameRoom, Player, PlayerPosition

router = APIRouter()

class CreateRoomRequest(BaseModel):
    name: str

class JoinRoomRequest(BaseModel):
    player_name: str

# In-memory storage for demo (will be replaced with database)
rooms: dict[str, GameRoom] = {}

@router.get("/rooms")
async def get_rooms() -> List[GameRoom]:
    """Get all game rooms"""
    return list(rooms.values())

@router.post("/rooms")
async def create_room(request: CreateRoomRequest) -> GameRoom:
    """Create a new game room"""
    import uuid
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
    if room.is_full:
        raise HTTPException(status_code=400, detail="Room is full")
    
    # 检查玩家是否已经在房间中
    existing_player = next((p for p in room.players if p.name == request.player_name), None)
    if existing_player:
        return room
    
    # Assign position based on current players
    positions = [PlayerPosition.NORTH, PlayerPosition.SOUTH, PlayerPosition.EAST, PlayerPosition.WEST]
    used_positions = {player.position for player in room.players}
    available_positions = [pos for pos in positions if pos not in used_positions]
    
    if not available_positions:
        raise HTTPException(status_code=400, detail="No available positions")
    
    import uuid
    player = Player(
        id=str(uuid.uuid4()),
        name=request.player_name,
        position=available_positions[0]
    )
    
    room.players.append(player)
    return room
