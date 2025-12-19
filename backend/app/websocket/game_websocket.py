"""
Game WebSocket handlers
"""
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
from typing import Dict, List, Optional
import json
import uuid
import asyncio
from app.game.game_state import GameState
from app.game.card_sorter import CardSorter
from app.api.game import rooms
from app.models.game import Card, Rank, Suit, GameRoom, Player, PlayerPosition
from app.services.stats_service import record_game_stats

router = APIRouter()


def parse_card_strings(card_strings: List[str]) -> List[Card]:
    """将前端传来的字符串列表转换为Card对象列表"""
    parsed_cards: List[Card] = []
    suit_map = {"♠": Suit.SPADES, "♥": Suit.HEARTS, "♣": Suit.CLUBS, "♦": Suit.DIAMONDS}
    for s in card_strings:
        try:
            if "JOKER-A" in s or "JOKER/大王" in s:
                parsed_cards.append(Card(rank=Rank.BIG_JOKER, is_joker=True))
            elif "JOKER-B" in s or "JOKER/小王" in s:
                parsed_cards.append(Card(rank=Rank.SMALL_JOKER, is_joker=True))
            else:
                suit_char = s[-1]
                rank_str = s[:-1]
                suit = suit_map.get(suit_char)
                rank = Rank(rank_str)
                parsed_cards.append(Card(rank=rank, suit=suit))
        except Exception:
            continue
    return parsed_cards

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
        # 存储每个房间的倒计时任务
        self.countdown_tasks: Dict[str, asyncio.Task] = {}
    
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
        # 必须先 accept，否则无法 close
        await websocket.accept()
        
        # 处理缺少 player_id 的兼容情况（仅允许 demo 房间）
        if not player_id:
            if room_id != "demo":
                await websocket.close(code=1008, reason="player_id required")
                return
            # demo 房间用于调试演示
            if room_id not in rooms:
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
        
        if room_id not in self.active_connections:
            self.active_connections[room_id] = []
        
        # 存储连接信息（包含player_id）
        conn_info = ConnectionInfo(websocket, player_id)
        self.active_connections[room_id].append(conn_info)
        
        # 如果房间存在但GameState不存在，创建它
        if room_id in rooms and room_id not in self.game_states:
            room = rooms[room_id]
            self.game_states[room_id] = GameState(
                room,
                level_up_mode=room.level_up_mode,
                ace_reset_enabled=room.ace_reset_enabled
            )
        
        # 连接成功后发送快照给当前玩家
        await self.send_snapshot(room_id, player_id)
        
        # 通知房间中所有其他玩家有新玩家加入（发送更新后的玩家列表）
        if room_id in rooms:
            room = rooms[room_id]
            gs = self.get_game_state(room_id)
            if gs:
                # 发送玩家列表更新事件给所有玩家（包括新加入的玩家）
                players_update = {
                    "type": "players_updated",
                    "players": [
                        {
                            "id": p.id,
                            "name": p.name,
                            "position": p.position.value,
                            "cards_count": len(p.cards)
                        }
                        for p in room.players
                    ],
                    "ready_to_start": {
                        "ready_count": len(gs.players_ready_to_start) if hasattr(gs, "players_ready_to_start") else 0,
                        "total_players": len(room.players),
                        "ready_players": list(gs.players_ready_to_start) if hasattr(gs, "players_ready_to_start") else []
                    } if gs.game_phase == "waiting" else None
                }
                await self.broadcast_to_room(json.dumps(players_update), room_id)
    
    async def disconnect(self, websocket: WebSocket, room_id: str):
        """断开连接"""
        disconnected_player_id = None
        if room_id in self.active_connections:
            # 找到要断开的玩家ID
            for conn in self.active_connections[room_id]:
                if conn.websocket == websocket:
                    disconnected_player_id = conn.player_id
                    break
            
            # 移除连接
            self.active_connections[room_id] = [
                conn for conn in self.active_connections[room_id]
                if conn.websocket != websocket
            ]
            if not self.active_connections[room_id]:
                del self.active_connections[room_id]
        
        # 通知房间中其他玩家有玩家离开（发送更新后的玩家列表）
        if room_id in rooms and disconnected_player_id:
            room = rooms[room_id]
            gs = self.get_game_state(room_id)
            if gs:
                # 发送玩家列表更新事件给所有剩余玩家
                players_update = {
                    "type": "players_updated",
                    "players": [
                        {
                            "id": p.id,
                            "name": p.name,
                            "position": p.position.value,
                            "cards_count": len(p.cards)
                        }
                        for p in room.players
                    ],
                    "ready_to_start": {
                        "ready_count": len(gs.players_ready_to_start) if hasattr(gs, "players_ready_to_start") else 0,
                        "total_players": len(room.players),
                        "ready_players": list(gs.players_ready_to_start) if hasattr(gs, "players_ready_to_start") else []
                    } if gs.game_phase == "waiting" else None
                }
                await self.broadcast_to_room(json.dumps(players_update), room_id)
    
    async def send_personal_message(self, message: str, websocket: WebSocket):
        """发送个人消息"""
        await websocket.send_text(message)
    
    async def start_countdown(self, room_id: str):
        """
        开始房间的倒计时（如果 max_play_time 为 0，则不启动倒计时）
        """
        print(f"[倒计时] 开始倒计时 - 房间: {room_id}")
        # 停止现有的倒计时任务
        await self.stop_countdown(room_id)
        
        # 获取游戏状态并重置和启动倒计时
        if room_id in self.game_states:
            game_state = self.game_states[room_id]
            # 如果 max_play_time 为 0，则不启动倒计时
            if game_state.max_play_time == 0:
                print(f"[倒计时] 房间 {room_id} 设置为不限制时长，不启动倒计时")
                game_state.start_countdown()  # 调用后会设置 countdown_active = False
                return
            game_state.start_countdown()  # 调用GameState的start_countdown方法激活倒计时
            print(f"[倒计时] 房间 {room_id} 的倒计时已激活 - 当前时间: {game_state.current_countdown}秒")
        else:
            return
        
        # 创建新的倒计时任务
        task = asyncio.create_task(self._countdown_loop(room_id))
        self.countdown_tasks[room_id] = task
        print(f"[倒计时] 为房间 {room_id} 创建新的倒计时任务")
    
    async def stop_countdown(self, room_id: str):
        """
        停止房间的倒计时
        """
        if room_id in self.countdown_tasks:
            task = self.countdown_tasks[room_id]
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                print(f"[倒计时] 房间 {room_id} 的倒计时任务已取消")
            del self.countdown_tasks[room_id]
            print(f"[倒计时] 成功停止房间 {room_id} 的倒计时任务")
        else:
            print(f"[倒计时] 房间 {room_id} 没有正在运行的倒计时任务")
    
    async def _countdown_loop(self, room_id: str):
        """
        倒计时循环任务
        """
        try:
            print(f"[倒计时] 启动倒计时循环 - 房间: {room_id}")
            while True:
                await asyncio.sleep(1)
                
                # 获取游戏状态
                if room_id not in self.game_states:
                    print(f"[倒计时] 房间 {room_id} 不存在，退出倒计时循环")
                    break
                
                game_state = self.game_states[room_id]
                
                # 如果 max_play_time 为 0，则不限制时长，退出倒计时循环
                if game_state.max_play_time == 0:
                    print(f"[倒计时] 房间 {room_id} 设置为不限制时长，退出倒计时循环")
                    break
                
                # 只在游戏阶段（playing）和有当前玩家时进行倒计时
                if game_state.game_phase != "playing" or not game_state.current_player:
                    print(f"[倒计时] 房间 {room_id} 不满足倒计时条件 - 阶段: {game_state.game_phase}, 当前玩家: {game_state.current_player}")
                    continue
                
                # 获取当前玩家信息
                current_player = game_state.get_player_by_position(game_state.current_player)
                player_info = f"ID: {current_player.id}, 名称: {current_player.name}, 位置: {game_state.current_player.value}" if current_player else "未知玩家"
                
                # 记录倒计时前的状态
                print(f"[倒计时] 房间 {room_id} - 当前玩家: {player_info}, 倒计时前: {game_state.current_countdown}秒, 激活状态: {game_state.countdown_active}")
                
                # 减少倒计时
                time_up = game_state.decrease_countdown()
                
                # 记录倒计时后的状态
                print(f"[倒计时] 房间 {room_id} - 当前玩家: {player_info}, 倒计时后: {game_state.current_countdown}秒, 时间到: {time_up}")
                
                # 发送倒计时更新
                print(f"[倒计时] 房间 {room_id} - 广播倒计时更新: {game_state.current_countdown}秒")
                await self._broadcast_countdown_update(room_id, game_state.current_countdown)
                
                # 如果时间到，触发自动出牌
                if time_up:
                    print(f"[倒计时] 房间 {room_id} - 倒计时结束，执行自动出牌")
                    await self._auto_play(room_id)
                    break
        except asyncio.CancelledError:
            pass
        except Exception as e:
            print(f"倒计时循环错误 ({room_id}): {e}")
    
    async def _broadcast_countdown_update(self, room_id: str, remaining_time: int):
        """
        广播倒计时更新给房间内所有玩家
        """
        # 获取游戏状态以检查倒计时激活状态
        if room_id in self.game_states:
            game_state = self.game_states[room_id]
            countdown_active = game_state.countdown_active
        else:
            countdown_active = True  # 默认值
        
        message = {
            "type": "countdown_updated",
            "remaining_time": remaining_time,
            "countdown_active": countdown_active
        }
        print(f"[倒计时] 准备广播倒计时更新 - 房间: {room_id}, 剩余时间: {remaining_time}秒, 激活状态: {countdown_active}, 消息内容: {message}")
        
        # 使用现有的broadcast_to_room方法发送消息
        await self.broadcast_to_room(json.dumps(message), room_id)
        print(f"[倒计时] 成功广播倒计时更新 - 房间: {room_id}, 剩余时间: {remaining_time}秒")
    
    async def _auto_play(self, room_id: str):
        """
        当倒计时结束时自动出牌
        """
        if room_id not in self.game_states:
            return
        
        game_state = self.game_states[room_id]
        
        # 调用GameState的auto_play方法
        result = game_state.auto_play()
        
        # 如果自动出牌成功，处理出牌结果
        if result.get("success", False):
            # 获取当前玩家
            player = game_state.get_player_by_id(game_state.current_player_id)
            if not player:
                return
            
            # 检查是否完成一轮（必须在play_card之后检查，因为play_card会更新状态）
            # 注意：play_card中如果一轮完成，会保存last_trick但不清空current_trick_with_player（延迟清空）
            # 所以这里检查：如果current_trick_with_player长度为4，说明刚完成一轮
            trick_was_complete = len(game_state.current_trick_with_player) == 4
            
            # 构建卡牌字符串列表（用于前端显示）
            # play_card已经更新了current_trick_with_player，其中的cards已经按手牌顺序排序
            # 直接从最后一条记录获取即可
            cards_str = []
            if hasattr(game_state, "current_trick_with_player") and game_state.current_trick_with_player:
                last_entry = game_state.current_trick_with_player[-1]
                cards_str = last_entry.get("cards", [])
            
            # 获取当前轮次最大玩家名称
            current_trick_max_player_name = None
            if hasattr(game_state, "current_trick_max_player_id") and game_state.current_trick_max_player_id:
                max_player = game_state.get_player_by_id(game_state.current_trick_max_player_id)
                if max_player:
                    current_trick_max_player_name = max_player.name
            
            # 构建出牌事件（包含play_type用于前端显示提示）
            play_event = {
                "type": "card_played",
                "player_id": game_state.current_player_id,
                "player_position": player.position.value,
                "cards": cards_str,
                "current_trick": game_state.current_trick_with_player if hasattr(game_state, "current_trick_with_player") else [],
                "trick_complete": trick_was_complete,
                "current_player": game_state.current_player.value if game_state.current_player else None,
                "current_trick_max_player": current_trick_max_player_name,
                "play_type": result.get("play_type")  # 添加play_type字段
            }
            
            # 广播出牌事件给所有玩家
            await self.broadcast_to_room(json.dumps(play_event), room_id)
            
            # 如果一轮结束，发送获胜者信息和上一轮出牌
            if trick_was_complete and hasattr(game_state, "last_trick"):
                # 使用last_trick作为current_trick，因为last_trick是上一轮完成时的数据
                trick_complete_event = {
                    "type": "trick_complete",
                    "last_trick": game_state.last_trick,
                    "current_trick": game_state.last_trick.copy(),  # 使用last_trick作为current_trick（用于延迟显示）
                    "tricks_won": game_state.tricks_won,
                    "idle_score": game_state.idle_score,  # 添加分数信息
                    "current_player": game_state.current_player.value if game_state.current_player else None
                }
                await self.broadcast_to_room(json.dumps(trick_complete_event), room_id)
                
                # 发送分数更新事件
                score_event = {
                    "type": "score_updated",
                    "idle_score": game_state.idle_score
                }
                await self.broadcast_to_room(json.dumps(score_event), room_id)
                
                # 发送完事件后，清空current_trick_with_player（为下一轮准备）
                game_state.current_trick_with_player = []
            
            # 发送状态快照
            await self.send_snapshot(room_id)
            
            # 检查游戏是否结束
            if game_state.game_phase == "scoring" and game_state.round_summary:
                # 记录战绩（仅记录一次）
                if not game_state.stats_recorded:
                    asyncio.create_task(record_game_stats(game_state.round_summary, game_state.room.players))
                    game_state.stats_recorded = True
                
                round_end_event = {
                    "type": "round_end",
                    "round_summary": game_state.round_summary,
                    "ready_count": len(game_state.players_ready_for_next_round),
                    "total_players": len(game_state.room.players),
                    "ready_players": list(game_state.players_ready_for_next_round)
                }
                await self.broadcast_to_room(json.dumps(round_end_event), room_id)
            else:
                # 重置倒计时，为下一个玩家开始倒计时
                await self.start_countdown(room_id)
    
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
                sorter = CardSorter(
                    current_level=gs.card_system.current_level,
                    trump_suit=gs.trump_suit
                )
                sorted_cards = sorter.sort_cards(player.cards)
                my_hand = [str(card) for card in sorted_cards]
        
        dealer = gs.get_dealer() if gs else None
        snapshot = {
            "type": "state_snapshot",
            "room_id": room_id,
            "room_name": gs.room.name if gs and gs.room else None,
            "owner_id": gs.room.owner_id if gs and gs.room else None,
            "current_level": gs.card_system.current_level if gs and gs.card_system else None,  # 庄家级别（用于级牌判断）
            "north_south_level": gs.north_south_level if gs else None,
            "east_west_level": gs.east_west_level if gs else None,
            "phase": gs.game_phase,
            "dealer_position": gs.dealer_position.value if gs.dealer_position else None,
            "dealer_player_id": dealer.id if dealer else None,
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
            "dealer_has_bottom": gs.dealer_has_bottom,
            "bottom_pending": getattr(gs, "bottom_pending", False),
            "idle_score": gs.idle_score,
            "tricks_won": gs.tricks_won,
            "my_hand": my_hand,  # 只有自己的手牌
            "countdown": gs.current_countdown,
            "countdown_active": gs.countdown_active,
            "play_time_limit": gs.room.play_time_limit if gs and gs.room else 18,  # 出牌等待时间限制（0表示不限制）
            "ace_reset_enabled": gs.ace_reset_enabled if gs else True,  # 打A重置是否启用
            "players_cards_count": {
                p.position.value: len(p.cards) for p in gs.room.players
            },
            "bidding_cards": {
                p_id: [str(card) for card in cards]
                for p_id, cards in getattr(gs, "bidding_display_cards", {}).items()
            } if hasattr(gs, "bidding_display_cards") else {}
        }
        # 亮主状态（若存在）
        try:
            snapshot["bidding"] = gs.get_bidding_status()
        except Exception:
            pass
        if player_id and dealer and player_id == dealer.id and gs.bottom_cards:
            snapshot["bottom_cards"] = [str(card) for card in gs.bottom_cards]
        
        # 添加新加入的底牌信息（仅在庄家获得底牌后且尚未扣底时）
        if player_id and dealer and player_id == dealer.id and gs.dealer_has_bottom and gs.bottom_pending:
            # 使用原始底牌（不会被扣底替换）
            if hasattr(gs, 'original_bottom_cards') and gs.original_bottom_cards:
                snapshot["newly_added_bottom_cards"] = [str(card) for card in gs.original_bottom_cards]
        
        # 添加当前轮次和上一轮出牌信息
        if hasattr(gs, "current_trick_with_player"):
            snapshot["current_trick"] = gs.current_trick_with_player
        if hasattr(gs, "last_trick"):
            snapshot["last_trick"] = gs.last_trick
        # 添加当前轮次最大玩家信息
        if hasattr(gs, "current_trick_max_player_id") and gs.current_trick_max_player_id:
            max_player = gs.get_player_by_id(gs.current_trick_max_player_id)
            if max_player:
                snapshot["current_trick_max_player_id"] = gs.current_trick_max_player_id
                snapshot["current_trick_max_player_name"] = max_player.name
        # 添加当前应该出牌的玩家
        # 优先使用GameState的current_player（实时更新）
        if hasattr(gs, "current_player") and gs.current_player:
            snapshot["current_player"] = gs.current_player.value
        # 如果没有current_player，尝试使用CardPlayingSystem的expected_leader（作为后备）
        elif gs.card_playing_system and hasattr(gs.card_playing_system, "expected_leader"):
            expected_leader = gs.card_playing_system.expected_leader
            if expected_leader:
                snapshot["current_player"] = expected_leader.value
        else:
            snapshot["current_player"] = None
        
        # 添加本局总结信息（如果在scoring阶段）
        if hasattr(gs, "round_summary") and gs.round_summary:
            snapshot["round_summary"] = gs.round_summary
            # 添加ready状态
            snapshot["ready_for_next_round"] = {
                "ready_count": len(gs.players_ready_for_next_round),
                "total_players": len(gs.room.players),
                "ready_players": list(gs.players_ready_for_next_round)
            }
        
        # 添加开始游戏的ready状态（waiting阶段）
        if gs.game_phase == "waiting":
            snapshot["ready_to_start"] = {
                "ready_count": len(gs.players_ready_to_start),
                "total_players": len(gs.room.players),
                "ready_players": list(gs.players_ready_to_start)
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
                        if dealer and conn.player_id == dealer.id:
                            if gs.bottom_cards:
                                personal_snapshot["bottom_cards"] = [str(card) for card in gs.bottom_cards]
                            # 添加新加入的底牌信息（仅在庄家获得底牌后且尚未扣底时）
                            if gs.dealer_has_bottom and gs.bottom_pending:
                                if hasattr(gs, 'original_bottom_cards') and gs.original_bottom_cards:
                                    personal_snapshot["newly_added_bottom_cards"] = [str(card) for card in gs.original_bottom_cards]
                        else:
                            personal_snapshot.pop("bottom_cards", None)
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
            elif msg_type == "ready_to_start_game":
                # 玩家准备开始游戏
                gs = manager.get_game_state(room_id)
                if not gs or not player_id_current:
                    await manager.send_personal_message(json.dumps({"type": "error", "message": "无法准备开始游戏"}), websocket)
                else:
                    result = gs.ready_to_start_game(player_id_current)
                    if result.get("success"):
                        # 广播ready状态更新
                        ready_event = {
                            "type": "ready_to_start_updated",
                            "player_id": player_id_current,
                            "ready_count": result.get("ready_count", 0),
                            "total_players": result.get("total_players", 0),
                            "all_ready": result.get("all_ready", False),
                            "ready_players": result.get("ready_players", [])
                        }
                        await manager.broadcast_to_room(json.dumps(ready_event), room_id)
                        
                        # 如果所有玩家都ready，游戏已自动开始，发送snapshot和phase_changed
                        if result.get("game_started"):
                            await manager.send_snapshot(room_id)
                            phase_event = {
                                "type": "phase_changed",
                                "phase": "dealing"
                            }
                            await manager.broadcast_to_room(json.dumps(phase_event), room_id)
                            
                            # 自动开始发牌（类似之前的auto_deal功能）
                            async def auto_deal_task():
                                gs = manager.get_game_state(room_id)
                                if gs:
                                    while gs.dealt_count < 100 and gs.game_phase == "dealing":
                                        await manager.handle_deal_tick(room_id)
                                        await asyncio.sleep(0.1)  # 每0.1秒发一张牌
                                    
                                    # 发牌完成后，发送snapshot和phase_changed事件
                                    if gs.game_phase == "bidding":
                                        await manager.send_snapshot(room_id)
                                        phase_event = {
                                            "type": "phase_changed",
                                            "phase": "bidding"
                                        }
                                        await manager.broadcast_to_room(json.dumps(phase_event), room_id)
                            
                            asyncio.create_task(auto_deal_task())
                    else:
                        await manager.send_personal_message(json.dumps({"type": "error", "message": result.get("message", "准备失败")}), websocket)
            elif msg_type == "cancel_ready_to_start_game":
                # 玩家取消准备开始游戏
                gs = manager.get_game_state(room_id)
                if not gs or not player_id_current:
                    await manager.send_personal_message(json.dumps({"type": "error", "message": "无法取消准备"}), websocket)
                else:
                    result = gs.cancel_ready_to_start_game(player_id_current)
                    if result.get("success"):
                        # 广播取消准备状态更新
                        ready_event = {
                            "type": "ready_to_start_updated",
                            "player_id": player_id_current,
                            "ready_count": result.get("ready_count", 0),
                            "total_players": result.get("total_players", 0),
                            "all_ready": False,
                            "ready_players": result.get("ready_players", [])
                        }
                        await manager.broadcast_to_room(json.dumps(ready_event), room_id)
                    else:
                        await manager.send_personal_message(json.dumps({"type": "error", "message": result.get("message", "取消准备失败")}), websocket)
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
                    cards_str = message.get("cards") or []
                    parsed_cards = parse_card_strings(cards_str)
                    result = gs.make_bid(player_id_current, parsed_cards)
                    
                    # 使用 bidding_display_cards 来显示前端定主区域的牌
                    # bidding_display_cards 已经包含了完整的对子（包括凑对时的 prev_card）
                    display_bidding_cards = {
                        p_id: [str(card) for card in cards]
                        for p_id, cards in getattr(gs, "bidding_display_cards", {}).items()
                    } if hasattr(gs, "bidding_display_cards") else {}
                    
                    bid_payload = {
                        "type": "bidding_updated",
                        "result": result,
                        "bidding": gs.get_bidding_status(),
                        "bidding_cards": display_bidding_cards,
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
                                for p_id, cards in getattr(gs, "bidding_display_cards", {}).items()
                            } if hasattr(gs, "bidding_display_cards") else {},
                            "turn_player_id": gs.bidding_turn_player_id
                        }
                        await manager.broadcast_to_room(json.dumps(payload), room_id)
                        if result.get("finished"):
                            await manager.broadcast_to_room(json.dumps({"type": "phase_changed", "phase": gs.game_phase}), room_id)
                        await manager.send_snapshot(room_id)
                    else:
                        await manager.send_personal_message(json.dumps({"type": "error", "message": result.get("message", "不可亮主")}), websocket)
            elif msg_type == "submit_bottom":
                gs = manager.get_game_state(room_id)
                if not gs or not player_id_current:
                    await manager.send_personal_message(json.dumps({"type": "error", "message": "无法扣底"}), websocket)
                else:
                    dealer = gs.get_dealer()
                    if not dealer or dealer.id != player_id_current:
                        await manager.send_personal_message(json.dumps({"type": "error", "message": "仅庄家可以扣底"}), websocket)
                    elif not gs.bottom_pending:
                        await manager.send_personal_message(json.dumps({"type": "error", "message": "当前不需要扣底"}), websocket)
                    else:
                        cards_str = message.get("cards") or []
                        parsed_cards = parse_card_strings(cards_str)
                        success = gs.dealer_discard_bottom(parsed_cards)
                        if success:
                            payload = {
                                "type": "bottom_updated",
                                "bottom_cards_count": len(gs.bottom_cards),
                                "dealer_has_bottom": gs.dealer_has_bottom,
                                "bottom_pending": gs.bottom_pending,
                                "dealer_player_id": dealer.id,
                                "phase": gs.game_phase
                            }
                            await manager.broadcast_to_room(json.dumps(payload), room_id)
                            if gs.game_phase == "playing":
                                await manager.broadcast_to_room(json.dumps({"type": "phase_changed", "phase": "playing"}), room_id)
                                # 游戏进入playing阶段时启动倒计时
                                await manager.start_countdown(room_id)
                            await manager.send_snapshot(room_id)
                        else:
                            await manager.send_personal_message(json.dumps({"type": "error", "message": "扣底失败，请检查所选牌"}), websocket)
            elif msg_type == "finish_bidding":
                gs = manager.get_game_state(room_id)
                if not gs:
                    await manager.send_personal_message(json.dumps({"type": "error", "message": "不可结束亮主"}), websocket)
                else:
                    ok = gs.finish_bidding()
                    if ok:
                        await manager.broadcast_to_room(json.dumps({"type": "phase_changed", "phase": gs.game_phase}), room_id)
                        # 如果进入playing阶段，启动倒计时
                        if gs.game_phase == "playing":
                            await manager.start_countdown(room_id)
                    await manager.send_snapshot(room_id)
            elif msg_type == "select_cards":
                # 玩家选择卡牌（用于自动出牌功能）
                gs = manager.get_game_state(room_id)
                if not gs or not player_id_current:
                    await manager.send_personal_message(json.dumps({"type": "error", "message": "无法处理选中卡牌"}), websocket)
                else:
                    # 检查是否轮到当前玩家出牌
                    player = gs.get_player_by_id(player_id_current)
                    if not player:
                        await manager.send_personal_message(json.dumps({"type": "error", "message": "玩家不存在"}), websocket)
                    else:
                        # 解析选中的卡牌
                        cards_str = message.get("cards") or []
                        if not isinstance(cards_str, list):
                            cards_str = [cards_str]
                        
                        # 将字符串转换为Card对象
                        parsed_cards = parse_card_strings(cards_str)
                        
                        # 更新GameState中的选中卡牌
                        gs.selected_cards = parsed_cards
                        
                        # 可以选择发送确认消息给前端
                        await manager.send_personal_message(json.dumps({"type": "cards_selected", "success": True}), websocket)
            elif msg_type == "play_card":
                # 玩家出牌（支持多张牌）
                gs = manager.get_game_state(room_id)
                if not gs or not player_id_current:
                    await manager.send_personal_message(json.dumps({"type": "error", "message": "无法出牌"}), websocket)
                else:
                    # 检查是否轮到当前玩家出牌
                    player = gs.get_player_by_id(player_id_current)
                    if not player:
                        await manager.send_personal_message(json.dumps({"type": "error", "message": "玩家不存在"}), websocket)
                    else:
                        # 检查出牌顺序：优先使用current_player（实时更新）
                        expected_position = None
                        if gs.current_player:
                            # 优先使用GameState的current_player（实时更新）
                            expected_position = gs.current_player
                        elif len(gs.current_trick_with_player) == 0:
                            # 第一轮，应该由庄家领出
                            expected_position = gs.dealer_position
                        elif gs.card_playing_system and hasattr(gs.card_playing_system, "expected_leader") and gs.card_playing_system.expected_leader:
                            # 如果没有current_player，使用expected_leader（作为后备）
                            expected_position = gs.card_playing_system.expected_leader
                        else:
                            # 后续轮次，按逆时针顺序
                            last_player_pos = gs.current_trick_with_player[-1]["player_position"]
                            positions = [PlayerPosition.NORTH, PlayerPosition.WEST, PlayerPosition.SOUTH, PlayerPosition.EAST]
                            last_pos = next((p for p in positions if p.value == last_player_pos), None)
                            if last_pos:
                                last_idx = positions.index(last_pos)
                                next_idx = (last_idx + 1) % 4
                                expected_position = positions[next_idx]
                        
                        if expected_position and player.position != expected_position:
                            await manager.send_personal_message(json.dumps({"type": "error", "message": f"未轮到您出牌，应由{expected_position.value}出牌"}), websocket)
                            continue
                        
                        # 解析卡牌（支持多张）
                        cards_str = message.get("cards") or message.get("card")  # 兼容单张和多张
                        if not cards_str:
                            await manager.send_personal_message(json.dumps({"type": "error", "message": "请选择要出的牌"}), websocket)
                        else:
                            # 转换为列表格式
                            if isinstance(cards_str, str):
                                cards_str = [cards_str]
                            
                            # 将字符串转换为Card对象
                            parsed_cards = parse_card_strings(cards_str)
                            if not parsed_cards:
                                await manager.send_personal_message(json.dumps({"type": "error", "message": "无效的卡牌"}), websocket)
                            else:
                                result = gs.play_card(player_id_current, parsed_cards)
                                if result.get("success"):
                                    # 玩家手动出牌成功，停止当前倒计时
                                    await manager.stop_countdown(room_id)
                                    # 检查是否完成一轮（必须在play_card之后检查，因为play_card会更新状态）
                                    # 注意：play_card中如果一轮完成，会保存last_trick但不清空current_trick_with_player（延迟清空）
                                    # 所以这里检查：如果current_trick_with_player长度为4，说明刚完成一轮
                                    trick_was_complete = len(gs.current_trick_with_player) == 4
                                    
                                    # 广播出牌事件（确保current_player已经更新）
                                    # 获取当前轮次最大玩家名称
                                    current_trick_max_player_name = None
                                    if hasattr(gs, "current_trick_max_player_id") and gs.current_trick_max_player_id:
                                        max_player = gs.get_player_by_id(gs.current_trick_max_player_id)
                                        if max_player:
                                            current_trick_max_player_name = max_player.name
                                    
                                    play_event = {
                                        "type": "card_played",
                                        "player_id": player_id_current,
                                        "player_position": player.position.value,
                                        "cards": cards_str,  # 改为cards列表
                                        "current_trick": gs.current_trick_with_player if hasattr(gs, "current_trick_with_player") else [],
                                        "trick_complete": trick_was_complete,
                                        "current_player": gs.current_player.value if gs.current_player else None,
                                        "current_trick_max_player": current_trick_max_player_name
                                    }
                                    await manager.broadcast_to_room(json.dumps(play_event), room_id)
                                    
                                    # 如果一轮结束，发送获胜者信息和上一轮出牌
                                    if trick_was_complete and hasattr(gs, "last_trick"):
                                        # 在清空之前保存当前轮次的牌（用于前端延迟显示）
                                        # 此时current_trick_with_player还包含上一轮的数据（在play_card中未清空）
                                        # 使用last_trick作为current_trick，因为last_trick是上一轮完成时的数据
                                        trick_complete_event = {
                                            "type": "trick_complete",
                                            "last_trick": gs.last_trick,
                                            "current_trick": gs.last_trick.copy(),  # 使用last_trick作为current_trick（用于延迟显示）
                                            "tricks_won": gs.tricks_won,
                                            "idle_score": gs.idle_score,  # 添加分数信息
                                            "current_player": gs.current_player.value if gs.current_player else None
                                        }
                                        await manager.broadcast_to_room(json.dumps(trick_complete_event), room_id)
                                        # 发送分数更新事件
                                        score_event = {
                                            "type": "score_updated",
                                            "idle_score": gs.idle_score
                                        }
                                        await manager.broadcast_to_room(json.dumps(score_event), room_id)
                                        # 发送完事件后，清空current_trick_with_player（为下一轮准备）
                                        gs.current_trick_with_player = []
                                    
                                    await manager.send_snapshot(room_id)
                                    
                                    # 无论是否一轮结束，为下一个玩家启动倒计时
                                    await manager.start_countdown(room_id)
                                    
                                    # 检查游戏是否结束（所有玩家手牌为空）
                                    # 注意：_handle_game_end会在play_card中调用，所以这里检查phase是否为scoring
                                    if gs.game_phase == "scoring" and gs.round_summary:
                                        # 记录战绩（仅记录一次）
                                        if not gs.stats_recorded:
                                            asyncio.create_task(record_game_stats(gs.round_summary, gs.room.players))
                                            gs.stats_recorded = True
                                        
                                        # 游戏结束，发送round_end事件
                                        round_end_event = {
                                            "type": "round_end",
                                            "round_summary": gs.round_summary,
                                            "ready_count": len(gs.players_ready_for_next_round),
                                            "total_players": len(gs.room.players),
                                            "ready_players": list(gs.players_ready_for_next_round)
                                        }
                                        await manager.broadcast_to_room(json.dumps(round_end_event), room_id)
                                else:
                                    # 出牌失败，检查是否是甩牌失败（有forced_cards）
                                    error_msg = result.get("message", "出牌失败")
                                    forced_cards = result.get("forced_cards")
                                    forced_cards_str = None
                                    if forced_cards:
                                        forced_cards_str = [str(card) for card in forced_cards]
                                    
                                    # 如果是甩牌失败（有forced_cards），先广播出牌事件让所有玩家看到甩出的牌
                                    if forced_cards_str:
                                        # 临时添加到current_trick_with_player用于显示（但不从手牌中移除）
                                        temp_trick_entry = {
                                            "player_id": player_id_current,
                                            "player_position": player.position.value,
                                            "cards": cards_str,
                                            "slingshot_failed": True  # 标记为甩牌失败
                                        }
                                        # 创建临时的current_trick用于显示
                                        temp_current_trick = gs.current_trick_with_player.copy()
                                        temp_current_trick.append(temp_trick_entry)
                                        
                                        # 广播出牌事件（让所有玩家看到甩出的牌）
                                        play_event = {
                                            "type": "card_played",
                                            "player_id": player_id_current,
                                            "player_position": player.position.value,
                                            "cards": cards_str,
                                            "current_trick": temp_current_trick,
                                            "trick_complete": False,
                                            "slingshot_failed": True,  # 标记为甩牌失败
                                            "current_player": gs.current_player.value if gs.current_player else None
                                        }
                                        await manager.broadcast_to_room(json.dumps(play_event), room_id)
                                        
                                        # 广播甩牌失败提示（让所有玩家都能看到）
                                        slingshot_failed_notification = {
                                            "type": "slingshot_failed_notification",
                                            "message": "首家甩牌失败，强制出小",
                                            "player_position": player.position.value,
                                            "player_name": player.name if hasattr(player, 'name') else None
                                        }
                                        await manager.broadcast_to_room(json.dumps(slingshot_failed_notification), room_id)
                                    
                                    # 发送错误信息（包含forced_cards）
                                    await manager.send_personal_message(json.dumps({"type": "error", "message": error_msg, "forced_cards": forced_cards_str, "slingshot_failed": bool(forced_cards_str)}), websocket)
            elif msg_type == "auto_deal":
                # 自动发牌（用于演示）
                if not room or not player_id_current or (room.owner_id and player_id_current != room.owner_id):
                    await manager.send_personal_message(json.dumps({"type": "error", "message": "只有房主可以自动发牌"}), websocket)
                else:
                    # 创建后台任务，不阻塞主循环
                    async def auto_deal_task():
                        gs = manager.get_game_state(room_id)
                        if gs:
                            while gs.dealt_count < 100 and gs.game_phase == "dealing":
                                await manager.handle_deal_tick(room_id)
                                await asyncio.sleep(0.1)
                    asyncio.create_task(auto_deal_task())
            elif msg_type == "auto_play":
                # 前端请求自动出牌（倒计时结束时触发）
                # 注意：实际的自动出牌逻辑由后端倒计时系统自动触发
                # 这里只是为了避免显示"Unknown message type"错误
                # 前端发送此消息主要是为了触发倒计时结束的处理
                # 但后端已经通过倒计时系统自动处理了，所以这里不需要额外操作
                pass
            elif msg_type == "ready_for_next_round":
                # 玩家准备进入下一轮
                gs = manager.get_game_state(room_id)
                if not gs or not player_id_current:
                    await manager.send_personal_message(json.dumps({"type": "error", "message": "无法准备下一轮"}), websocket)
                else:
                    result = gs.ready_for_next_round(player_id_current)
                    if result.get("success"):
                        # 广播ready状态更新
                        ready_event = {
                            "type": "ready_for_next_round_updated",
                            "player_id": player_id_current,
                            "ready_count": result.get("ready_count", 0),
                            "total_players": result.get("total_players", 0),
                            "all_ready": result.get("all_ready", False),
                            "ready_players": result.get("ready_players", [])  # 包含所有已准备玩家的ID列表
                        }
                        await manager.broadcast_to_room(json.dumps(ready_event), room_id)
                        
                        # 如果所有玩家都ready，自动开始下一轮
                        if result.get("all_ready"):
                            if gs.start_next_round():
                                # 下一轮已开始，进入发牌阶段
                                await manager.broadcast_to_room(json.dumps({"type": "phase_changed", "phase": "dealing"}), room_id)
                                await manager.send_snapshot(room_id)
                                
                                # 自动开始发牌（类似ready_to_start_game的逻辑）
                                async def auto_deal_task():
                                    gs = manager.get_game_state(room_id)
                                    if gs:
                                        while gs.dealt_count < 100 and gs.game_phase == "dealing":
                                            await manager.handle_deal_tick(room_id)
                                            await asyncio.sleep(0.1)  # 每0.1秒发一张牌
                                asyncio.create_task(auto_deal_task())
                    else:
                        await manager.send_personal_message(json.dumps({"type": "error", "message": result.get("message", "准备失败")}), websocket)
            else:
                # 其他消息类型可以后续扩展
                await manager.send_personal_message(
                    json.dumps({"type": "error", "message": f"Unknown message type: {msg_type}"}),
                    websocket
                )
            
    except WebSocketDisconnect:
        await manager.disconnect(websocket, room_id)
