"""
Game WebSocket handlers
"""
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
from typing import Dict, List, Optional
import json
from app.game.game_state import GameState
from app.api.game import rooms

router = APIRouter()

# Store active connections
class ConnectionInfo:
    """连接信息，包含WebSocket和player_id"""
    def __init__(self, websocket: WebSocket, player_id: str):
        self.websocket = websocket
        self.player_id = player_id

class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, List[ConnectionInfo]] = {}
        # 存储每个房间的GameState实例
        self.game_states: Dict[str, GameState] = {}
    
    async def connect(self, websocket: WebSocket, room_id: str, player_id: str):
        """
        连接WebSocket
        
        Args:
            websocket: WebSocket连接
            room_id: 房间ID
            player_id: 玩家ID（必须已在房间中）
        """
        # 验证房间和玩家
        if room_id not in rooms:
            await websocket.close(code=1008, reason="Room not found")
            return
        
        room = rooms[room_id]
        # 验证玩家是否在房间中
        player = None
        for p in room.players:
            if p.id == player_id:
                player = p
                break
        
        if not player:
            await websocket.close(code=1008, reason="Player not in room")
            return
        
        await websocket.accept()
        
        if room_id not in self.active_connections:
            self.active_connections[room_id] = []
        
        # 存储连接信息（包含player_id）
        conn_info = ConnectionInfo(websocket, player_id)
        self.active_connections[room_id].append(conn_info)
        
        # 如果房间存在但GameState不存在，创建它
        if room_id in rooms and room_id not in self.game_states:
            self.game_states[room_id] = GameState(rooms[room_id])
        
        # 连接成功后发送快照（只发送给当前玩家）
        await self.send_snapshot(room_id, player_id)
    
    def disconnect(self, websocket: WebSocket, room_id: str):
        """断开连接"""
        if room_id in self.active_connections:
            self.active_connections[room_id] = [
                conn for conn in self.active_connections[room_id]
                if conn.websocket != websocket
            ]
            if not self.active_connections[room_id]:
                del self.active_connections[room_id]
    
    async def send_personal_message(self, message: str, websocket: WebSocket):
        """发送个人消息"""
        await websocket.send_text(message)
    
    async def send_to_player(self, message: str, room_id: str, player_id: str):
        """发送消息给特定玩家"""
        if room_id in self.active_connections:
            for conn in self.active_connections[room_id]:
                if conn.player_id == player_id:
                    try:
                        await conn.websocket.send_text(message)
                    except:
                        # 连接已断开，移除
                        self.active_connections[room_id].remove(conn)
                    break
    
    async def broadcast_to_room(self, message: str, room_id: str, exclude_player_id: Optional[str] = None):
        """广播消息到房间所有玩家（可排除特定玩家）"""
        if room_id in self.active_connections:
            for conn in self.active_connections[room_id]:
                if exclude_player_id and conn.player_id == exclude_player_id:
                    continue
                try:
                    await conn.websocket.send_text(message)
                except:
                    # Remove broken connections
                    if room_id in self.active_connections:
                        self.active_connections[room_id].remove(conn)
    
    def get_game_state(self, room_id: str) -> Optional[GameState]:
        """获取房间的GameState实例"""
        return self.game_states.get(room_id)
    
    async def send_snapshot(self, room_id: str, player_id: Optional[str] = None):
        """
        发送状态快照
        
        Args:
            room_id: 房间ID
            player_id: 玩家ID，如果提供则只发送给该玩家，否则广播给所有人
        """
        gs = self.get_game_state(room_id)
        if not gs:
            return
        
        # 获取该玩家的手牌（如果提供了player_id）
        my_hand = []
        if player_id:
            player = gs.get_player_by_id(player_id)
            if player:
                # 获取排序后的手牌
                from app.game.card_sorter import CardSorter
                sorter = CardSorter(
                    current_level=gs.card_system.current_level,
                    trump_suit=gs.trump_suit
                )
                sorted_cards = sorter.sort_cards(player.cards)
                my_hand = [str(card) for card in sorted_cards]
        
        snapshot = {
            "type": "state_snapshot",
            "room_id": room_id,
            "phase": gs.game_phase,
            "dealer_position": gs.dealer_position.value if gs.dealer_position else None,
            "trump_suit": gs.trump_suit.value if gs.trump_suit else None,
            "dealt_count": gs.dealt_count,
            "players": [
                {
                    "id": p.id,
                    "name": p.name,
                    "position": p.position.value,
                    "cards_count": len(p.cards)  # 其他玩家的手牌数量（不显示具体牌）
                }
                for p in gs.room.players
            ],
            "bottom_cards_count": len(gs.bottom_cards),
            "scores": gs.scores,
            "tricks_won": gs.tricks_won,
            "my_hand": my_hand  # 只有自己的手牌
        }
        
        if player_id:
            # 只发送给特定玩家
            await self.send_to_player(json.dumps(snapshot), room_id, player_id)
        else:
            # 广播给所有人（但每个玩家收到的手牌不同）
            # 需要为每个玩家单独发送
            if room_id in self.active_connections:
                for conn in self.active_connections[room_id]:
                    # 为每个玩家生成个性化的快照
                    player = gs.get_player_by_id(conn.player_id)
                    if player:
                        from app.game.card_sorter import CardSorter
                        sorter = CardSorter(
                            current_level=gs.card_system.current_level,
                            trump_suit=gs.trump_suit
                        )
                        sorted_cards = sorter.sort_cards(player.cards)
                        personal_hand = [str(card) for card in sorted_cards]
                        personal_snapshot = snapshot.copy()
                        personal_snapshot["my_hand"] = personal_hand
                        try:
                            await conn.websocket.send_text(json.dumps(personal_snapshot))
                        except:
                            self.active_connections[room_id].remove(conn)
    
    async def handle_deal_tick(self, room_id: str):
        """处理发牌tick"""
        gs = self.get_game_state(room_id)
        if not gs:
            error_msg = {
                "type": "error",
                "message": "GameState not found for room"
            }
            await self.broadcast_to_room(json.dumps(error_msg), room_id)
            return
        
        result = gs.deal_tick()
        if result.get("success"):
            # 获取该玩家的手牌（已经在deal_tick中使用insert_sorted排序好了）
            player_pos = result.get("player")
            player = None
            for p in gs.room.players:
                if p.position.value == player_pos:
                    player = p
                    break
            
            # 直接使用player.cards（已经通过insert_sorted保持排序）
            sorted_cards = []
            if player:
                # player.cards已经通过insert_sorted保持排序，直接转换为字符串列表
                sorted_cards = [str(card) for card in player.cards]
            
            # 发送deal_tick事件，只发送给收到牌的玩家（包含排序后的完整手牌）
            # 其他玩家只收到基本信息（不包含手牌）
            if player:
                # 发送给收到牌的玩家（包含完整手牌）
                event_with_hand = {
                    "type": "deal_tick",
                    "player": result.get("player"),
                    "card": result.get("card"),
                    "dealt_count": result.get("dealt_count"),
                    "sorted_hand": sorted_cards  # 该玩家的排序后完整手牌
                }
                await self.send_to_player(json.dumps(event_with_hand), room_id, player.id)
            
            # 发送给其他玩家（不包含手牌）
            event_public = {
                "type": "deal_tick",
                "player": result.get("player"),
                "card": None,  # 不显示具体牌
                "dealt_count": result.get("dealt_count"),
                "sorted_hand": None  # 不显示手牌
            }
            if player:
                await self.broadcast_to_room(json.dumps(event_public), room_id, exclude_player_id=player.id)
            else:
                await self.broadcast_to_room(json.dumps(event_public), room_id)
            
            # 如果发牌完成，发送阶段变化和快照
            if result.get("done"):
                phase_event = {
                    "type": "phase_changed",
                    "phase": "bidding"
                }
                await self.broadcast_to_room(json.dumps(phase_event), room_id)
                # 为每个玩家发送个性化的快照
                await self.send_snapshot(room_id)
        else:
            # 发送错误消息
            error_msg = {
                "type": "error",
                "message": result.get("message", "Deal tick failed")
            }
            await self.broadcast_to_room(json.dumps(error_msg), room_id)

manager = ConnectionManager()

@router.websocket("/{room_id}")
async def websocket_endpoint(websocket: WebSocket, room_id: str, player_id: str = Query(None)):
    """
    WebSocket endpoint for game room
    
    Args:
        room_id: 房间ID
        player_id: 玩家ID（查询参数，可选。如果不提供，会创建测试玩家）
    """
    # 如果没有提供player_id，创建测试玩家（兼容旧代码）
    if not player_id:
        # 如果房间不存在，创建测试房间
        if room_id not in rooms:
            from app.models.game import GameRoom, Player, PlayerPosition
            import uuid
            test_room = GameRoom(id=room_id, name=f"测试房间-{room_id}")
            # 创建4个测试玩家
            for pos in [PlayerPosition.NORTH, PlayerPosition.WEST, PlayerPosition.SOUTH, PlayerPosition.EAST]:
                player = Player(
                    id=str(uuid.uuid4()),
                    name=f"测试玩家-{pos.value}",
                    position=pos,
                    is_ready=True
                )
                test_room.players.append(player)
            rooms[room_id] = test_room
        
        # 使用第一个玩家作为默认玩家
        room = rooms[room_id]
        if room.players:
            player_id = room.players[0].id
        else:
            # 如果没有玩家，创建一个
            from app.models.game import Player, PlayerPosition
            import uuid
            player = Player(
                id=str(uuid.uuid4()),
                name="测试玩家",
                position=PlayerPosition.NORTH,
                is_ready=True
            )
            room.players.append(player)
            player_id = player.id
    
    await manager.connect(websocket, room_id, player_id)
    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            
            # Handle different message types
            msg_type = message.get("type")
            
            if msg_type == "ping":
                await manager.send_personal_message(
                    json.dumps({"type": "pong"}), 
                    websocket
                )
            elif msg_type == "start_game":
                # 开始游戏
                gs = manager.get_game_state(room_id)
                if not gs:
                    error_msg = {
                        "type": "error",
                        "message": "GameState not found for room"
                    }
                    await manager.broadcast_to_room(json.dumps(error_msg), room_id)
                elif gs.start_game():
                    await manager.send_snapshot(room_id)
                    phase_event = {
                        "type": "phase_changed",
                        "phase": "dealing"
                    }
                    await manager.broadcast_to_room(json.dumps(phase_event), room_id)
                else:
                    error_msg = {
                        "type": "error",
                        "message": "Failed to start game (check if room is ready)"
                    }
                    await manager.broadcast_to_room(json.dumps(error_msg), room_id)
            elif msg_type == "deal_tick":
                # 发一张牌
                await manager.handle_deal_tick(room_id)
            elif msg_type == "auto_deal":
                # 自动发牌（用于演示）
                # 创建后台任务，不阻塞主循环
                import asyncio
                async def auto_deal_task():
                    gs = manager.get_game_state(room_id)
                    if gs:
                        while gs.dealt_count < 100 and gs.game_phase == "dealing":
                            await manager.handle_deal_tick(room_id)
                            await asyncio.sleep(0.2)
                asyncio.create_task(auto_deal_task())
            else:
                # 其他消息类型可以后续扩展
                await manager.send_personal_message(
                    json.dumps({"type": "error", "message": f"Unknown message type: {msg_type}"}),
                    websocket
                )
            
    except WebSocketDisconnect:
        manager.disconnect(websocket, room_id)
