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
    
    def get_connection_info(self, room_id: str, websocket: WebSocket) -> Optional[ConnectionInfo]:
        """根据websocket获取连接信息"""
        for conn in self.active_connections.get(room_id, []):
            if conn.websocket == websocket:
                return conn
        return None

    def get_player_id_by_connection(self, room_id: str, websocket: WebSocket) -> Optional[str]:
        conn = self.get_connection_info(room_id, websocket)
        return conn.player_id if conn else None
    
    async def connect(self, websocket: WebSocket, room_id: str, player_id: str):
        """
        连接WebSocket
        
        Args:
            websocket: WebSocket连接
            room_id: 房间ID
            player_id: 玩家ID（必须已在房间中）
        """
        # 处理缺少 player_id 的兼容情况（仅允许 demo 房间）
        if not player_id:
            if room_id != "demo":
                await websocket.close(code=1008, reason="player_id required")
                return
            # demo 房间用于调试演示
            if room_id not in rooms:
                from app.models.game import GameRoom, Player, PlayerPosition
                import uuid
                test_room = GameRoom(id=room_id, name=f"测试房间-{room_id}")
                for pos in [PlayerPosition.NORTH, PlayerPosition.WEST, PlayerPosition.SOUTH, PlayerPosition.EAST]:
                    player = Player(
                        id=str(uuid.uuid4()),
                        name=f"测试玩家-{pos.value}",
                        position=pos,
                        is_ready=True
                    )
                    test_room.players.append(player)
                test_room.owner_id = test_room.players[0].id
                rooms[room_id] = test_room
            room = rooms[room_id]
            # 使用第一个玩家作为默认连接的玩家
            if room.players:
                player_id = room.players[0].id
            else:
                from app.models.game import Player, PlayerPosition
                import uuid
                player = Player(
                    id=str(uuid.uuid4()),
                    name="测试玩家",
                    position=PlayerPosition.NORTH,
                    is_ready=True
                )
                room.players.append(player)
                room.owner_id = player.id
                player_id = player.id
        else:
            if room_id not in rooms:
                await websocket.close(code=1008, reason="Room not found")
                return
            room = rooms[room_id]
            # 验证玩家是否在房间中
            player = next((p for p in room.players if p.id == player_id), None)
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
            "room_name": gs.room.name if gs and gs.room else None,
            "owner_id": gs.room.owner_id if gs and gs.room else None,
            "current_level": gs.card_system.current_level if gs and gs.card_system else None,
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
            "my_hand": my_hand,  # 只有自己的手牌
            "players_cards_count": {
                p.position.value: len(p.cards) for p in gs.room.players
            },
            "bidding_cards": {
                p_id: [str(card) for card in cards]
                for p_id, cards in getattr(gs, "bidding_cards", {}).items()
            } if hasattr(gs, "bidding_cards") else {}
        }
        # 亮主状态（若存在）
        try:
            snapshot["bidding"] = gs.get_bidding_status()
        except Exception:
            pass
        
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
                        personal_snapshot["players_cards_count"] = {
                            pos.position.value: len(pos.cards) for pos in gs.room.players
                        }
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
                    "sorted_hand": sorted_cards,  # 该玩家的排序后完整手牌
                    "players_cards_count": result.get("players_cards_count"),
                }
                await self.send_to_player(json.dumps(event_with_hand), room_id, player.id)
            
            # 发送给其他玩家（不包含手牌）
            event_public = {
                "type": "deal_tick",
                "player": result.get("player"),
                "card": None,  # 不显示具体牌
                "dealt_count": result.get("dealt_count"),
                "sorted_hand": None,  # 不显示手牌
                "players_cards_count": result.get("players_cards_count"),
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
    # 如果由于校验失败未被接受，则直接结束协程，避免未accept时读取导致异常
    if manager.get_connection_info(room_id, websocket) is None:
        return
    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            
            # Handle different message types
            msg_type = message.get("type")
            conn_info = manager.get_connection_info(room_id, websocket)
            player_id_current = conn_info.player_id if conn_info else None
            room = rooms.get(room_id)
            
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
                elif not room:
                    await manager.send_personal_message(json.dumps({"type": "error", "message": "Room not found"}), websocket)
                elif not player_id_current or (room.owner_id and player_id_current != room.owner_id):
                    await manager.send_personal_message(json.dumps({"type": "error", "message": "只有房主可以开始游戏"}), websocket)
                elif not room.can_start:
                    await manager.send_personal_message(json.dumps({"type": "error", "message": "需要4名玩家才能开始游戏"}), websocket)
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
                if not room or not player_id_current or (room.owner_id and player_id_current != room.owner_id):
                    await manager.send_personal_message(json.dumps({"type": "error", "message": "只有房主可以发牌"}), websocket)
                else:
                    await manager.handle_deal_tick(room_id)
            elif msg_type == "make_bid":
                # 亮主/反主
                gs = manager.get_game_state(room_id)
                if not gs or not player_id_current:
                    await manager.send_personal_message(json.dumps({"type": "error", "message": "不可亮主"}), websocket)
                else:
                    # 将前端的字符串牌转换为Card
                    from app.models.game import Card, Rank, Suit
                    cards_str = message.get("cards") or []
                    parsed_cards = []
                    for s in cards_str:
                        try:
                            if "JOKER-A" in s:
                                parsed_cards.append(Card(rank=Rank.BIG_JOKER, is_joker=True))
                            elif "JOKER-B" in s:
                                parsed_cards.append(Card(rank=Rank.SMALL_JOKER, is_joker=True))
                            else:
                                # 形如 "10♥" "A♣"
                                suit_char = s[-1]
                                rank_str = s[:-1]
                                suit_map = {"♠": Suit.SPADES, "♥": Suit.HEARTS, "♣": Suit.CLUBS, "♦": Suit.DIAMONDS}
                                suit = suit_map.get(suit_char)
                                rank = Rank(rank_str)
                                parsed_cards.append(Card(rank=rank, suit=suit))
                        except Exception:
                            continue
                    result = gs.make_bid(player_id_current, parsed_cards)
                    bid_payload = {
                        "type": "bidding_updated",
                        "result": result,
                        "bidding": gs.get_bidding_status(),
                        "bidding_cards": {
                            p_id: [str(card) for card in cards]
                            for p_id, cards in getattr(gs, "bidding_cards", {}).items()
                        } if hasattr(gs, "bidding_cards") else {},
                        "turn_player_id": gs.bidding_turn_player_id
                    }
                    await manager.broadcast_to_room(json.dumps(bid_payload), room_id)
                    # 若已经决定了主牌，发snapshot
                    await manager.send_snapshot(room_id)
            elif msg_type == "pass_bid":
                gs = manager.get_game_state(room_id)
                if not gs or not player_id_current:
                    await manager.send_personal_message(json.dumps({"type": "error", "message": "不可亮主"}), websocket)
                else:
                    result = gs.pass_bid(player_id_current)
                    if result.get("success"):
                        payload = {
                            "type": "bidding_updated",
                            "result": result,
                            "bidding": gs.get_bidding_status(),
                            "bidding_cards": {
                                p_id: [str(card) for card in cards]
                                for p_id, cards in getattr(gs, "bidding_cards", {}).items()
                            } if hasattr(gs, "bidding_cards") else {},
                            "turn_player_id": gs.bidding_turn_player_id
                        }
                        await manager.broadcast_to_room(json.dumps(payload), room_id)
                        if result.get("finished"):
                            await manager.broadcast_to_room(json.dumps({"type": "phase_changed", "phase": gs.game_phase}), room_id)
                        await manager.send_snapshot(room_id)
                    else:
                        await manager.send_personal_message(json.dumps({"type": "error", "message": result.get("message", "不可亮主")}), websocket)
            elif msg_type == "finish_bidding":
                gs = manager.get_game_state(room_id)
                if not gs:
                    await manager.send_personal_message(json.dumps({"type": "error", "message": "不可结束亮主"}), websocket)
                else:
                    ok = gs.finish_bidding()
                    if ok:
                        await manager.broadcast_to_room(json.dumps({"type": "phase_changed", "phase": gs.game_phase}), room_id)
                    await manager.send_snapshot(room_id)
            elif msg_type == "auto_deal":
                # 自动发牌（用于演示）
                if not room or not player_id_current or (room.owner_id and player_id_current != room.owner_id):
                    await manager.send_personal_message(json.dumps({"type": "error", "message": "只有房主可以自动发牌"}), websocket)
                else:
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
