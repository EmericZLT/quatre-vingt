"""
八十分游戏状态管理
"""
from typing import List, Optional, Dict, Any
from datetime import datetime
import random
import asyncio
from app.models.game import GameRoom, Player, PlayerPosition, GameStatus, Suit, Card, Rank
from app.game.card_system import CardSystem
from app.game.bidding_system import BiddingSystem
from app.game.card_sorter import CardSorter
from app.game.card_playing import CardPlayingSystem
from app.game.leveling import calculate_level_up


class GameState:
    """游戏状态管理类"""
    
    def __init__(self, room: GameRoom, level_up_mode: str = "default", ace_reset_enabled: bool = True):
        self.room = room
        self.card_system = CardSystem()
        self.bidding_system = BiddingSystem(self.card_system.current_level)
        self.trump_suit: Optional[Suit] = None
        # 南北家和东西家独立级别（初始都是2）
        self.north_south_level: int = 2  # 南北家级别
        self.east_west_level: int = 2    # 东西家级别
        # 升级模式：控制使用哪个升级函数（"default", "standard" 等）
        self.level_up_mode: str = level_up_mode
        # 打A重置：连续3次打A不过是否重置级别
        self.ace_reset_enabled: bool = ace_reset_enabled
        self.dealer_position: PlayerPosition = PlayerPosition.NORTH
        self.current_player: PlayerPosition = PlayerPosition.NORTH
        self.current_trick: List[Card] = []  # 保持向后兼容，但实际使用current_trick_with_player
        self.current_trick_with_player: List[Dict[str, Any]] = []  # 存储 {player_id, player_position, card}
        self.last_trick: List[Dict[str, Any]] = []  # 上一轮出牌信息
        self.trick_leader: Optional[PlayerPosition] = None
        # 倒计时相关属性（从房间配置中读取）
        self.max_play_time: int = room.play_time_limit  # 最大出牌时间（秒），从房间配置读取
        self.current_countdown: int = self.max_play_time  # 当前倒计时剩余时间
        self.countdown_active: bool = False  # 倒计时是否处于激活状态
        self.countdown_task: Optional[asyncio.Task] = None  # 倒计时任务引用
        
        # 当前玩家ID（用于WebSocket通信）
        self.current_player_id: Optional[str] = None
        # 当前玩家选中的卡牌（用于自动出牌功能）
        self.selected_cards: Optional[List[Card]] = None
        # game_phase 状态说明：
        # - "waiting": 等待状态（初始状态，或一局结束后）
        #   * 变化时机：__init__() 初始化时，end_round() 结束时
        # - "dealing": 发牌阶段
        #   * 变化时机：start_game() 开始游戏时
        #   * 变化到 "bidding"：deal_tick() 发完100张牌时
        # - "bidding": 亮主阶段（发牌完成后，玩家可以亮主/反主）
        #   * 变化时机：deal_tick() 发完100张牌时
        #   * 变化到 "bottom"：finish_bidding() 指定庄家并等待扣底
        # - "bottom": 扣底阶段（仅庄家操作）
        #   * 变化时机：finish_bidding() 指定庄家后，庄家拿到底牌
        #   * 变化到 "playing"：庄家完成扣底
        # - "playing": 游戏阶段（出牌阶段）
        #   * 变化时机：finish_bidding() 或 _determine_trump_from_bottom() 完成时
        #   * 变化到 "waiting"：end_round() 结束一局时
        # - "scoring": 计分阶段（目前未使用，保留用于未来扩展）
        self.game_phase = "waiting"
        self.idle_score = 0  # 闲家得分（庄家不计分）
        self.tricks_won = {"north_south": 0, "east_west": 0}
        self.bottom_cards: List[Card] = []  # 底牌，始终8张
        self.original_bottom_cards: List[Card] = []  # 原始底牌（用于高亮显示，不会被替换）
        self.dealer_has_bottom = False  # 庄家是否已获得底牌
        # 发牌流程（逐张、逆时针）：NORTH -> WEST -> SOUTH -> EAST -> ...
        self.dealing_order: List[PlayerPosition] = [
            PlayerPosition.NORTH,
            PlayerPosition.WEST,
            PlayerPosition.SOUTH,
            PlayerPosition.EAST,
        ]
        self.next_deal_turn_index: int = 0
        self.dealing_deck: List[Card] = []  # 前100张作为发牌区
        self.trump_locked: bool = False  # 定主完成后锁定主牌
        self.dealt_count: int = 0  # 已发出的牌（应至多100）
        self.bidding_cards: Dict[str, List[Card]] = {}  # 记录每个玩家亮主时打出的牌，用于最后归还 {player_id: [cards]}
        self.bidding_display_cards: Dict[str, List[Card]] = {}  # 记录每个玩家当前定主区域显示的牌 {player_id: [cards]}
        self.is_first_round: bool = True  # 是否为第一局游戏
        self.fixed_dealer_position: Optional[PlayerPosition] = None  # 第一局确定后固定的庄家
        self.bottom_pending: bool = False  # 是否等待庄家扣底
        self.bidding_turn_player_id: Optional[str] = None
        self._bidding_queue: List[str] = []
        self.card_playing_system: Optional[CardPlayingSystem] = None  # 出牌系统，在trump_suit确定后初始化
        self.current_trick_max_player_id: Optional[str] = None  # 当前轮次中牌更大的玩家ID
        self.players_ready_for_next_round: set = set()  # 已准备好进入下一轮的玩家ID集合
        self.players_ready_to_start: set = set()  # 已准备好开始游戏的玩家ID集合（waiting阶段使用）
        self.round_summary: Optional[Dict[str, Any]] = None  # 本局游戏总结信息
        self.bottom_bonus_info: Optional[Dict[str, Any]] = None  # 扣底信息：{"bottom_score": int, "multiplier": int, "bonus": int}
        # 打A次数统计（用于惩罚连续打A但未胜利的一方）
        self.north_south_ace_count: int = 0  # 南北方坐庄且级牌为A的次数
        self.east_west_ace_count: int = 0    # 东西方坐庄且级牌为A的次数
        self.stats_recorded: bool = False   # 是否已记录本局战绩
    
    def _reset_round_state(self):
        """
        重置一轮游戏的状态（在新一轮开始时调用）
        包含所有需要清空的游戏状态
        
        注意：不清空 players_ready_* 状态，这些由调用方根据需要清空
        """
        # 游戏阶段和锁定状态
        self.room.status = GameStatus.PLAYING
        self.game_phase = "dealing"
        self.trump_locked = False
        
        # 主牌相关
        self.trump_suit = None
        self.room.trump_suit = None
        self.card_playing_system = None  # 确保使用新的trump_suit重新初始化
        
        # 底牌相关
        self.dealer_has_bottom = False
        self.bottom_pending = False
        self.original_bottom_cards = []
        self.bottom_bonus_info = None
        
        # 亮主相关
        self.bidding_turn_player_id = None
        self._bidding_queue = []
        self.bidding_cards = {}
        self.bidding_display_cards = {}
        
        # 出牌相关
        self.current_trick = []
        self.current_trick_with_player = []
        self.last_trick = []
        self.trick_leader = None
        
        # 分数
        self.idle_score = 0
        
        # 总结信息（新一轮开始时清空）
        self.round_summary = None
        self.stats_recorded = False
        
        # 重置倒计时
        if self.max_play_time > 0:
            self.current_countdown = self.max_play_time
        else:
            self.current_countdown = 0
        self.countdown_active = False
        self.countdown_task = None
        
    def start_game(self) -> bool:
        """开始游戏（当所有玩家都准备时自动调用）"""
        # 检查是否有4名玩家
        if len(self.room.players) != 4:
            return False
        
        # 检查是否所有玩家都准备（在waiting阶段）
        if self.game_phase == "waiting":
            if len(self.players_ready_to_start) != 4:
                return False
        
        if self.fixed_dealer_position is not None:
            self.dealer_position = self.fixed_dealer_position
        
        # 重置一轮游戏的状态
        self._reset_round_state()
        
        # 清空准备状态（第一局特有）
        self.players_ready_for_next_round = set()
        self.players_ready_to_start = set()
        
        # 创建并洗牌
        deck = self.card_system.create_deck()
        self.card_system.shuffle_deck()
        
        # 前100张作为发牌区，后8张作为底牌
        self.dealing_deck = deck[0:100]
        self.bottom_cards = deck[100:108]
        
        # 清空玩家手牌
        for p in self.room.players:
            p.cards = []
        
        # 发牌顺序：第一局随机选择一名玩家开始，后续局从庄家开始
        if self.is_first_round:
            # 第一局：随机选择一名玩家作为发牌起始位置
            first_dealer = random.choice(self.dealing_order)
            self._set_dealing_order_from_position(first_dealer)
        else:
            # 后续局：从庄家开始
            self._set_dealing_order_from_dealer()
        
        self.dealt_count = 0
        return True
    
    def set_trump_suit(self, suit: Suit) -> bool:
        """直接设置主牌花色（仅用于管理接口）。锁定后不可更改。"""
        if self.trump_locked:
            return False
        if self.game_phase not in ["dealing", "bidding"]:
            return False
        
        self.trump_suit = suit
        self.room.trump_suit = suit
        return True
    
    def give_bottom_to_dealer(self) -> bool:
        """庄家获得底牌"""
        if self.dealer_has_bottom:
            return False
        
        dealer = self.get_dealer()
        if not dealer:
            return False
        
        # 保存原始底牌（用于高亮显示）
        self.original_bottom_cards = self.bottom_cards.copy()
        
        # 庄家获得底牌（33张牌），保持手牌有序
        sorter = CardSorter(
            current_level=self.card_system.current_level,
            trump_suit=self.trump_suit
        )
        dealer.cards = sorter.insert_many_sorted(dealer.cards, self.bottom_cards)
        self.dealer_has_bottom = True
        self.bottom_pending = True
        return True
    
    def dealer_discard_bottom(self, cards_to_discard: List[Card]) -> bool:
        """庄家扣底（从手中扣出8张牌作为新底牌）"""
        if not self.dealer_has_bottom:
            return False
        if self.game_phase != "bottom":
            return False
        
        if not cards_to_discard:
            return False
        
        dealer = self.get_dealer()
        if not dealer:
            return False
        
        if self.bottom_cards:
            expected_len = len(self.bottom_cards)
            if len(cards_to_discard) != expected_len:
                return False
        else:
            # 默认要求8张
            if len(cards_to_discard) != 8:
                return False
        
        # 检查庄家是否有这些牌
        for card in cards_to_discard:
            if card not in dealer.cards:
                return False
        
        # 移除庄家手中的牌
        for card in cards_to_discard:
            dealer.cards.remove(card)
        
        # 设置新的底牌
        self.bottom_cards = [card.copy() if hasattr(card, "copy") else card for card in cards_to_discard]
        
        # 同步更新 card_playing_system 的底牌（如果已初始化）
        if self.card_playing_system:
            self.card_playing_system.bottom_cards = self.bottom_cards.copy()
        
        # 重新整理庄家手牌
        sorter = CardSorter(
            current_level=self.card_system.current_level,
            trump_suit=self.trump_suit
        )
        dealer.cards = sorter.sort_cards(dealer.cards)
        self.bottom_pending = False
        
        # 清空原始底牌（扣底完成后不再需要高亮）
        self.original_bottom_cards = []
        self.game_phase = "playing"
        # 设置当前出牌玩家为庄家（第一轮由庄家领出）
        self.current_player = self.dealer_position
        # 更新当前玩家ID
        dealer = self.get_player_by_position(self.dealer_position)
        self.current_player_id = dealer.id if dealer else None
        # 重置expected_leader为None，确保第一轮由庄家领出
        if self.card_playing_system:
            self.card_playing_system.expected_leader = None
        return True
    
    def get_dealer(self) -> Optional[Player]:
        """获取庄家"""
        return self.get_player_by_position(self.dealer_position)
    
    def make_bid(self, player_id: str, cards: List[Card]) -> Dict[str, Any]:
        """玩家亮主"""
        if self.game_phase not in ["dealing", "bidding"]:
            return {"success": False, "message": "当前不可亮主"}
        
        # 检查玩家是否有这些牌
        player = self.get_player_by_id(player_id)
        if not player:
            return {"success": False, "message": "玩家不存在"}
        
        for card in cards:
            if card not in player.cards:
                return {"success": False, "message": "玩家没有这些牌"}
        
        # 获取该玩家之前打出的牌（用于凑对逻辑）
        previous_bidding_cards = self.bidding_cards.get(player_id, [])
        
        # 调用亮主系统（传递之前打出的牌，支持凑对逻辑）
        result = self.bidding_system.make_bid(player_id, cards, previous_bidding_cards)
        
        if result["success"]:
            # 1. 累积记录该玩家打出的牌（用于后续归还和前端显示）
            # 注意：只记录新打出的牌（cards），不重复记录之前已打出的牌
            if player_id not in self.bidding_cards:
                self.bidding_cards[player_id] = []
            
            for card in cards:
                self.bidding_cards[player_id].append(card.copy() if hasattr(card, "copy") else card)
            
            # 2. 更新该玩家定主区域显示的牌（用于前端显示）
            # 前端需要显示该玩家所有打出的牌，所以使用 bidding_cards
            if player_id not in self.bidding_display_cards:
                self.bidding_display_cards[player_id] = []
            
            for card in cards:
                self.bidding_display_cards[player_id].append(card.copy() if hasattr(card, "copy") else card)
            
            # 3. 从玩家手中移除亮主的牌（只移除新打出的牌，不移除之前已打出的牌）
            for card in cards:
                player.cards.remove(card)

            # 设置反主顺序（从该玩家的下家开始）
            self._prepare_bidding_turn(player)
        
        return result

    def pass_bid(self, player_id: str) -> Dict[str, Any]:
        """玩家选择不反主"""
        if self.game_phase not in ["dealing", "bidding"]:
            return {"success": False, "message": "当前不可亮主"}
        if player_id != self.bidding_turn_player_id:
            return {"success": False, "message": "未轮到该玩家"}

        # 移除当前玩家
        if self._bidding_queue and self._bidding_queue[0] == player_id:
            self._bidding_queue.pop(0)

        # 设置下一个玩家
        if self._bidding_queue:
            self.bidding_turn_player_id = self._bidding_queue[0]
            finished = False
        else:
            self.bidding_turn_player_id = None
            finished = False
            if self.is_dealing_complete() and self.bidding_system.current_bid:
                finished = self.finish_bidding()

        return {
            "success": True,
            "next_player": self.bidding_turn_player_id,
            "finished": finished
        }

    def finish_bidding(self) -> bool:
        """结束亮主阶段"""
        if self.game_phase not in ["bidding"]:
            return False
        # 必须发完100张牌后方可结束亮主
        if not self.is_dealing_complete():
            return False
        
        # 结束亮主
        final_bid = self.bidding_system.finish_bidding()
        
        if final_bid:
            # 设置主牌花色
            self.trump_suit = self.bidding_system.get_trump_suit()
            self.room.trump_suit = self.trump_suit
            
            # 归还所有参与亮主的玩家的牌（保持手牌有序）
            sorter = CardSorter(
                current_level=self.card_system.current_level,
                trump_suit=self.trump_suit
            )
            for player_id, cards_list in self.bidding_cards.items():
                player = self.get_player_by_id(player_id)
                if player and cards_list:
                    player.cards = sorter.insert_many_sorted(player.cards, cards_list)
            
            # 清空亮主记录
            self.bidding_cards = {}
            self.bidding_display_cards = {}
            self._bidding_queue = []
            self.bidding_turn_player_id = None
            
            # 找到最终亮主玩家，设置庄家
            winner_player = self.get_player_by_id(final_bid.player_id) if final_bid else None
            if winner_player:
                if self.fixed_dealer_position is None:
                    self.fixed_dealer_position = winner_player.position
                self.dealer_position = self.fixed_dealer_position or winner_player.position
            
            # 初始化出牌系统
            self._init_card_playing_system()
            
            # 庄家自动获得底牌，进入扣底阶段
            bottom_taken = self.give_bottom_to_dealer()
            self.bottom_pending = True if bottom_taken else False
            self.game_phase = "bottom" if bottom_taken else "playing"
            self.trump_locked = True
            return True
        else:
            # 无人亮主，翻底牌确定主牌
            return self._determine_trump_from_bottom()
    
    def _determine_trump_from_bottom(self) -> bool:
        """从底牌确定主牌花色"""
        if not self.bottom_cards:
            return False
        
        self.bottom_pending = False
        # 简化版本：选择底牌中第一张非王牌的花色
        for card in self.bottom_cards:
            if not card.is_joker:
                self.trump_suit = card.suit
                self.room.trump_suit = self.trump_suit
                # 初始化出牌系统
                self._init_card_playing_system()
                # 注意：庄家获得底牌的逻辑已解耦，需要单独调用 give_bottom_to_dealer()
                self.game_phase = "playing"
                self.trump_locked = True
                # 设置当前出牌玩家为庄家（第一轮由庄家领出）
                self.current_player = self.dealer_position
                # 重置expected_leader为None，确保第一轮由庄家领出
                if self.card_playing_system:
                    self.card_playing_system.expected_leader = None
                return True
        
        # 如果底牌全是王牌，设为无主
        self.trump_suit = None
        self.room.trump_suit = None
        # 注意：庄家获得底牌的逻辑已解耦，需要单独调用 give_bottom_to_dealer()
        self.game_phase = "playing"
        self.trump_locked = True
        return True

    def deal_tick(self) -> Dict[str, Any]:
        """发一张牌（逆时针下一位玩家），用于0.2s调用一次。发完100张后自动进入bidding阶段。"""
        if self.game_phase != "dealing":
            return {"success": False, "message": "当前不在发牌阶段"}
        # 若已达100张，切换阶段（兜底）
        if self.dealt_count >= 100:
            self.game_phase = "bidding"
            return {"success": True, "done": True, "message": "发牌已完成，进入亮主阶段"}
        
        # 取下一张牌
        card = self.dealing_deck.pop(0)
        # 发给下一位
        pos = self.dealing_order[self.next_deal_turn_index]
        player = self.get_player_by_position(pos)
        if not player:
            return {"success": False, "message": "目标玩家不存在"}
        # 增量插入到已排序手牌，保持摸牌过程中手牌有序
        sorter = CardSorter(
            current_level=self.card_system.current_level,
            trump_suit=self.trump_suit
        )
        player.cards = sorter.insert_sorted(player.cards, card)
        self.dealt_count += 1
        
        # 更新下一个顺位
        self.next_deal_turn_index = (self.next_deal_turn_index + 1) % len(self.dealing_order)
        
        # 如果本次发完了（空）
        done = False
        if self.dealt_count >= 100 or not self.dealing_deck:
            self.game_phase = "bidding"
            done = True
            # 若已有亮主，确保轮到下家继续反主
            if self.bidding_system.current_bid and not self.bidding_turn_player_id:
                winner = self.get_player_by_id(self.bidding_system.current_bid.player_id)
                if winner:
                    self._prepare_bidding_turn(winner)

        return {
            "success": True,
            "done": done,
            "player": pos.value,
            "card": str(card),
            "players_cards_count": {p.position.value: len(p.cards) for p in self.room.players},
            "dealt_count": self.dealt_count,
        }

    def is_dealing_complete(self) -> bool:
        """是否已发完100张（每人25张）"""
        return self.dealt_count >= 100
    
    def get_bidding_status(self) -> Dict[str, Any]:
        """获取亮主状态"""
        status = self.bidding_system.get_bidding_status()
        status["turn_player_id"] = self.bidding_turn_player_id
        return status
    
    def _init_card_playing_system(self):
        """初始化出牌系统（在trump_suit确定后调用）"""
        if self.trump_suit is not None or self.game_phase == "playing":
            # 确保使用最新的级别（庄家级别）来初始化系统
            # 因为级牌判断需要用到current_level
            self.card_playing_system = CardPlayingSystem(
                self.card_system,
                self.trump_suit
            )
            # 设置所有玩家的手牌（用于甩牌验证）
            all_hands = {
                player.position: player.cards
                for player in self.room.players
            }
            self.card_playing_system.set_player_hands(all_hands)
            # 设置底牌
            self.card_playing_system.bottom_cards = self.bottom_cards.copy()
            # 设置闲家位置（非庄家的一方）
            dealer_pos = self.dealer_position
            if dealer_pos in [PlayerPosition.NORTH, PlayerPosition.SOUTH]:
                self.card_playing_system.idle_positions = {PlayerPosition.EAST, PlayerPosition.WEST}
            else:
                self.card_playing_system.idle_positions = {PlayerPosition.NORTH, PlayerPosition.SOUTH}
    
    def play_card(self, player_id: str, cards: List[Card]) -> Dict[str, Any]:
        """
        玩家出牌（支持多张牌：单张、对子、连对、甩牌）
        
        Args:
            player_id: 玩家ID
            cards: 出的牌列表
            
        Returns:
            Dict包含success、message等信息
        """
        if self.game_phase != "playing":
            return {"success": False, "message": "当前不在出牌阶段"}
        
        # 找到出牌玩家
        player = self.get_player_by_id(player_id)
        if not player:
            return {"success": False, "message": "玩家不存在"}
        
        # 检查玩家是否有这些牌
        for card in cards:
            if card not in player.cards:
                return {"success": False, "message": f"玩家没有这张牌: {card}"}
        
        # 如果没有初始化出牌系统，初始化它
        if self.card_playing_system is None:
            self._init_card_playing_system()
        
        if self.card_playing_system is None:
            return {"success": False, "message": "出牌系统未初始化"}
        
        # 更新所有玩家的手牌（用于甩牌验证）
        all_hands = {
            p.position: p.cards
            for p in self.room.players
        }
        self.card_playing_system.set_player_hands(all_hands)
        
        # 检查是否是领出（在调用CardPlayingSystem之前检查，因为CardPlayingSystem会更新current_trick）
        is_leading = len(self.card_playing_system.current_trick) == 0 if self.card_playing_system else len(self.current_trick) == 0
        
        # 在调用play_card之前保存led_cards，因为play_card可能会在一轮完成时清空led_cards
        saved_led_cards = None
        if self.card_playing_system and not is_leading:
            saved_led_cards = self.card_playing_system.led_cards.copy() if self.card_playing_system.led_cards else None
        
        # 使用CardPlayingSystem处理出牌
        result = self.card_playing_system.play_card(player.position, cards, player.cards)
        
        if not result.success:
            return {"success": False, "message": result.message, "forced_cards": result.forced_cards}
        
        # 从玩家手牌中移除出的牌之前，先按照手牌中的顺序重新排序出牌
        # 这样确保显示顺序与手牌中的顺序一致，而不是玩家选中的顺序
        # 创建一个 cards 的副本用于标记匹配（处理重复牌的情况）
        cards_to_match = cards.copy()
        # 按照手牌中的顺序排序出牌
        sorted_cards = []
        for card_in_hand in player.cards:
            # 如果手牌中的这张牌在要出的牌列表中，且还没被匹配完
            if card_in_hand in cards_to_match:
                sorted_cards.append(card_in_hand)
                # 从待匹配列表中移除（只移除第一个匹配的，处理重复牌）
                cards_to_match.remove(card_in_hand)
                # 如果所有牌都已匹配，提前退出
                if not cards_to_match:
                    break
        
        # 从玩家手牌中移除出的牌
        for card in cards:
            player.cards.remove(card)
        
        # 更新current_trick_with_player（支持多张牌）
        # 使用按手牌顺序排序后的牌
        cards_str = [str(card) for card in sorted_cards]
        self.current_trick_with_player.append({
            "player_id": player_id,
            "player_position": player.position.value,
            "cards": cards_str  # 改为cards列表
        })
        
        # 保持向后兼容：current_trick只存储第一张牌
        if is_leading:
            self.current_trick.append(cards[0])
            self.trick_leader = player.position
            # 新的一轮开始，重置当前轮次最大玩家
            self.current_trick_max_player_id = player_id
        else:
            # 跟牌时，判断是否比当前最大玩家更大
            if self.current_trick_max_player_id and self.card_playing_system:
                # 如果led_cards被清空了（一轮完成时），临时恢复保存的值用于比较
                trick_completed = len(self.current_trick_with_player) == 4
                if saved_led_cards and not self.card_playing_system.led_cards:
                    self.card_playing_system.led_cards = saved_led_cards.copy()
                
                # 获取当前最大玩家的牌
                max_player = self.get_player_by_id(self.current_trick_max_player_id)
                if max_player:
                    # 找到当前最大玩家在当前轮次出的牌
                    max_player_cards = None
                    for entry in self.current_trick_with_player:
                        if entry["player_id"] == self.current_trick_max_player_id:
                            # 将字符串转换回Card对象
                            max_player_cards = []
                            for card_str in entry["cards"]:
                                parsed = self._parse_card_string(card_str)
                                if parsed:
                                    max_player_cards.append(parsed)
                            break
                    
                    if max_player_cards:
                        # 使用CardPlayingSystem的比较逻辑
                        if self.card_playing_system.compare_cards_in_trick(cards, max_player_cards):
                            # 当前玩家的牌更大，更新最大玩家
                            self.current_trick_max_player_id = player_id
                
                # 如果一轮已完成且我们临时恢复了led_cards，现在清空它（因为比较已完成）
                if trick_completed and saved_led_cards and self.card_playing_system.led_cards == saved_led_cards:
                    self.card_playing_system.led_cards = []
        
        # 如果一轮出完（4个玩家都出完），处理一轮完成逻辑
        if len(self.current_trick_with_player) == 4:
            winner = self._determine_trick_winner(result)
            if winner:
                self._handle_trick_completion(winner)
                
                # 检查是否所有玩家手牌都为空（游戏结束）
                all_hands_empty = all(len(p.cards) == 0 for p in self.room.players)
                if all_hands_empty and self.game_phase == "playing":
                    # 游戏结束，进入计分阶段
                    self._handle_game_end()
        else:
            # 如果还没完成一轮，更新current_player为下一个玩家（逆时针）
            # 无论是领出还是跟牌，都需要更新current_player
            positions = [PlayerPosition.NORTH, PlayerPosition.WEST, PlayerPosition.SOUTH, PlayerPosition.EAST]
            current_idx = positions.index(player.position)
            next_idx = (current_idx + 1) % 4
            self.current_player = positions[next_idx]
            # 更新当前玩家ID
            next_player = self.get_player_by_position(positions[next_idx])
            self.current_player_id = next_player.id if next_player else None
        
        # 如果一轮出完，winner已经在上面处理过了，这里返回None或者从current_trick_max_player_id获取
        winner = None
        if len(self.current_trick_with_player) == 4 and self.current_trick_max_player_id:
            winner_player = self.get_player_by_id(self.current_trick_max_player_id)
            if winner_player:
                winner = winner_player.position
        
        return {"success": True, "message": result.message, "winner": winner}
    
    def determine_trick_winner(self) -> str:
        """判断一圈的获胜者"""
        if len(self.current_trick) != 4:
            return ""
        
        # 简化版本：按出牌顺序判断
        # 实际应该根据主牌、副牌规则判断
        return "north_south"  # 临时返回
    
    def get_player_by_id(self, player_id: str) -> Optional[Player]:
        """根据ID获取玩家"""
        for player in self.room.players:
            if player.id == player_id:
                return player
        return None
    
    def get_player_by_position(self, position: PlayerPosition) -> Optional[Player]:
        """根据位置获取玩家"""
        for player in self.room.players:
            if player.position == position:
                return player
        return None
    
    def reset_countdown(self):
        """重置倒计时"""
        if self.max_play_time > 0:
            self.current_countdown = self.max_play_time
        else:
            self.current_countdown = 0
        self.countdown_active = False
    
    def start_countdown(self):
        """开始倒计时（如果 max_play_time 为 0，则不激活倒计时）"""
        if self.max_play_time > 0:
            self.current_countdown = self.max_play_time
            self.countdown_active = True
        else:
            self.current_countdown = 0
            self.countdown_active = False
    
    def stop_countdown(self):
        """停止倒计时"""
        self.countdown_active = False
    
    def decrease_countdown(self) -> bool:
        """减少倒计时1秒，返回是否倒计时已结束（如果 max_play_time 为 0，则永远不结束）"""
        if self.max_play_time == 0:
            return False  # 不限制时长，永远不结束
        if self.countdown_active and self.current_countdown > 0:
            self.current_countdown -= 1
            return self.current_countdown == 0
        return False
    
    def auto_play(self) -> Dict[str, Any]:
        """
        自动出牌 - 支持优先使用玩家选中的卡牌
        1. 若存在选中卡牌且符合当前出牌规则，则自动打出该选中卡牌
        2. 若未选中任何卡牌，或选中的卡牌不符合出牌规则，则自动触发原有的跟牌逻辑
        只关注规则合规性，不进行最优牌选择
        
        Returns:
            Dict包含success、message等信息
        """
        if self.game_phase != "playing":
            return {"success": False, "message": "当前不在出牌阶段"}
        
        # 获取当前玩家
        current_player = self.get_player_by_position(self.current_player)
        if not current_player:
            return {"success": False, "message": "当前玩家不存在"}
        
        # 如果没有初始化出牌系统，初始化它
        if self.card_playing_system is None:
            self._init_card_playing_system()
        
        if self.card_playing_system is None:
            return {"success": False, "message": "出牌系统未初始化"}
        
        # 检查当前游戏状态：是领出还是跟牌
        is_leading = len(self.card_playing_system.current_trick) == 0
        
        # 获取当前玩家的位置
        player_pos = current_player.position
        if not player_pos:
            return {"success": False, "message": "无法获取玩家位置"}
        
        # 优先检查并使用玩家选中的卡牌
        if self.selected_cards and len(self.selected_cards) > 0:
            # 验证选中的卡牌是否属于当前玩家
            for card in self.selected_cards:
                if card not in current_player.cards:
                    # 选中的卡牌不属于当前玩家，重置选中卡牌并继续使用原有逻辑
                    self.selected_cards = None
                    break
            
            if self.selected_cards:  # 确认所有选中的卡牌都属于当前玩家
                # 检查选中的卡牌数量是否符合当前轮次要求
                if is_leading:
                    # 领出时，任意数量的卡牌都可能符合规则，直接尝试出牌
                    result = self.play_card(current_player.id, self.selected_cards)
                    if result.get("success", False):
                        # 保存选中的卡牌用于返回结果
                        played_cards = self.selected_cards.copy()
                        # 重置选中卡牌
                        self.selected_cards = None
                        result['played_cards'] = played_cards
                        result['play_type'] = "selected_cards"
                        return result
                    else:
                        # 检查是否有强制要求出的牌（甩牌失败的情况）
                        forced_cards = result.get("forced_cards")
                        if forced_cards:
                            # 如果有强制要求出的牌，直接使用这些牌出牌
                            # 保存强制出的牌用于返回结果
                            result = self.play_card(current_player.id, forced_cards)
                            if result.get("success", False):
                                    # 重置选中卡牌
                                    self.selected_cards = None
                                    result['played_cards'] = forced_cards
                                    result['play_type'] = "selected_cards"
                                    return result
                        # 选中的卡牌不符合领出规则且没有强制出的牌，重置选中卡牌并继续使用原有逻辑
                        self.selected_cards = None
                else:
                    # 跟牌时，需要检查卡牌数量是否与领出的卡牌数量相同
                    led_card_count = len(self.card_playing_system.led_cards)
                    if len(self.selected_cards) == led_card_count:
                        # 检查选中的卡牌是否符合跟牌规则
                        check_result = self.card_playing_system._check_follow_rules(player_pos, self.selected_cards, current_player.cards)
                        if check_result.success:
                            # 选中的卡牌符合规则，尝试出牌
                            result = self.play_card(current_player.id, self.selected_cards)
                            if result.get("success", False):
                                # 保存选中的卡牌用于返回结果
                                played_cards = self.selected_cards.copy()
                                # 重置选中卡牌
                                self.selected_cards = None
                                result['played_cards'] = played_cards
                                result['play_type'] = "selected_cards"
                                return result
                            else:
                                # 选中的卡牌不符合规则，重置选中卡牌并继续使用原有逻辑
                                self.selected_cards = None
                        else:
                            # 选中的卡牌不符合跟牌规则，重置选中卡牌并继续使用原有逻辑
                            self.selected_cards = None
                    else:
                        # 选中的卡牌数量不符合要求，重置选中卡牌并继续使用原有逻辑
                        self.selected_cards = None
            
            # 选中的卡牌不符合规则或出牌失败，重置选中卡牌
            self.selected_cards = None
        
        # 创建打乱顺序的手牌列表，随机选择牌（对超时玩家更公平）
        import random
        shuffled_cards = current_player.cards.copy()
        random.shuffle(shuffled_cards)
        
        if is_leading:
            # 领出情况：从打乱后的列表中直接出第一张符合规则的单张牌
            for card in shuffled_cards:
                result = self.play_card(current_player.id, [card])
                if result.get("success", False):
                    result['played_cards'] = [card]
                    result['play_type'] = "auto_logic"
                    # 系统自动出牌成功后，清空选中的卡牌（避免下一轮误用）
                    self.selected_cards = None
                    return result
        else:
            # 跟牌情况：找到第一个符合规则的出牌组合
            led_card_count = len(self.card_playing_system.led_cards)
            
            # 使用打乱后的手牌列表生成所有可能的相同数量的组合
            from itertools import combinations
            all_combinations = list(combinations(shuffled_cards, led_card_count))
            
            # 遍历所有组合，找到第一个符合规则的组合
            for combo in all_combinations:
                combo_list = list(combo)
                
                # 直接调用_check_follow_rules方法验证是否符合跟牌规则
                check_result = self.card_playing_system._check_follow_rules(player_pos, combo_list, current_player.cards)
                
                if check_result.success:
                    # 找到符合规则的组合，尝试出牌
                    result = self.play_card(current_player.id, combo_list)
                    if result.get("success", False):
                        result['played_cards'] = combo_list
                        result['play_type'] = "auto_logic"
                        # 系统自动出牌成功后，清空选中的卡牌（避免下一轮误用）
                        self.selected_cards = None
                        return result
        
        # 如果没有找到可以出的牌，返回失败
        return {"success": False, "message": "没有找到可以出的牌"}
    
    def get_sorted_cards(self, player_id: str) -> List[Card]:
        """
        获取玩家的排序后手牌（用于前端展示）
        
        Args:
            player_id: 玩家ID
            
        Returns:
            排序后的手牌列表
        """
        player = self.get_player_by_id(player_id)
        if not player:
            return []
        
        sorter = CardSorter(
            current_level=self.card_system.current_level,
            trump_suit=self.trump_suit
        )
        
        return sorter.sort_cards(player.cards)
    
    def calculate_scores(self) -> int:
        """计算得分（返回闲家得分）"""
        return self.idle_score
    
    def calculate_next_dealer(self, idle_score: int) -> PlayerPosition:
        """
        根据本局闲家得分计算下一局的庄家位置
        
        Args:
            idle_score: 本局闲家得分
            
        Returns:
            下一局的庄家位置
        """
        current_dealer = self.dealer_position
        
        if idle_score < 80:
            # 闲家得分未达到80分：庄家变为对家
            # North <-> South, East <-> West
            partner_map = {
                PlayerPosition.NORTH: PlayerPosition.SOUTH,
                PlayerPosition.SOUTH: PlayerPosition.NORTH,
                PlayerPosition.EAST: PlayerPosition.WEST,
                PlayerPosition.WEST: PlayerPosition.EAST,
            }
            return partner_map[current_dealer]
        else:
            # 闲家得分达到80分：庄家变为下家（逆时针）
            # North -> West -> South -> East -> North
            next_dealer_map = {
                PlayerPosition.NORTH: PlayerPosition.WEST,
                PlayerPosition.WEST: PlayerPosition.SOUTH,
                PlayerPosition.SOUTH: PlayerPosition.EAST,
                PlayerPosition.EAST: PlayerPosition.NORTH,
            }
            return next_dealer_map[current_dealer]
    
    def end_round(self, idle_score: int) -> bool:
        """
        结束一局游戏，计算下一局的庄家
        
        Args:
            idle_score: 本局闲家得分
            
        Returns:
            是否成功结束
        """
        if self.game_phase != "playing":
            return False
        
        # 计算下一局的庄家（若已固定，则保持不变）
        if self.fixed_dealer_position is not None:
            self.dealer_position = self.fixed_dealer_position
        else:
            next_dealer = self.calculate_next_dealer(idle_score)
            self.dealer_position = next_dealer
        
        # 标记不再是第一局
        self.is_first_round = False
        
        # 只设置游戏阶段为等待状态
        # 不清空任何游戏数据，保留供前端查看（round_summary等）
        # 所有数据的清空将在下一轮start_next_round()时进行
        self.game_phase = "waiting"
        
        # 清空准备状态，等待玩家准备下一轮
        self.players_ready_for_next_round = set()
        
        return True
    
    def _set_dealing_order_from_dealer(self):
        """
        根据当前庄家位置设置发牌顺序（从庄家开始，逆时针）
        """
        dealer_index = self.dealing_order.index(self.dealer_position)
        
        # 重新排列发牌顺序：从庄家开始
        self.dealing_order = (
            self.dealing_order[dealer_index:] +
            self.dealing_order[:dealer_index]
        )
        
        # 设置下一个发牌索引为0（即庄家）
        self.next_deal_turn_index = 0
    
    def _set_dealing_order_from_position(self, position: PlayerPosition):
        """
        根据指定位置设置发牌顺序（从该位置开始，逆时针）
        
        Args:
            position: 发牌起始位置
        """
        position_index = self.dealing_order.index(position)
        
        # 重新排列发牌顺序：从指定位置开始
        self.dealing_order = (
            self.dealing_order[position_index:] +
            self.dealing_order[:position_index]
        )
        
        # 设置下一个发牌索引为0（即指定位置）
        self.next_deal_turn_index = 0
    
    def can_play_card(self, player_id: str, card: Card) -> bool:
        """检查玩家是否可以出这张牌"""
        player = self.get_player_by_id(player_id)
        if not player:
            return False
        
        # 检查玩家是否有这张牌
        if card not in player.cards:
            return False
        
        # 如果是第一张牌，可以出任何牌
        if len(self.current_trick) == 0:
            return True
        
        # 检查跟牌规则（简化版本）
        # 实际应该检查是否有该花色，是否必须跟牌等
        return True
    
    def get_game_status(self) -> Dict[str, Any]:
        """获取游戏状态"""
        status = {
            "room_id": self.room.id,
            "status": self.room.status.value,
            "phase": self.game_phase,
            "current_level": self.card_system.current_level,  # 庄家级别（用于级牌判断）
            "north_south_level": self.north_south_level,
            "east_west_level": self.east_west_level,
            "trump_suit": self.trump_suit.value if self.trump_suit else None,
            "current_player": self.current_player.value,
            "dealer_position": self.dealer_position.value,
            "dealer_has_bottom": self.dealer_has_bottom,
            "bottom_pending": self.bottom_pending,
            "dealer_player_id": self.get_dealer().id if self.get_dealer() else None,
            "bottom_cards_count": len(self.bottom_cards),
            "dealing_left": (100 - self.dealt_count) if self.game_phase == "dealing" else 0,
            "trump_locked": self.trump_locked,
            "players": [
                {
                    "id": player.id,
                    "name": player.name,
                    "position": player.position.value,
                    "cards_count": len(player.cards),
                    "is_ready": player.is_ready,
                    "is_dealer": player.position == self.dealer_position
                }
                for player in self.room.players
            ],
            "idle_score": self.idle_score,
            "tricks_won": self.tricks_won,
            "current_trick_max_player_id": self.current_trick_max_player_id
        }
        
        # 添加亮主状态
        if self.game_phase == "bidding":
            status["bidding"] = self.get_bidding_status()
        if hasattr(self, "bidding_cards"):
            status["bidding_cards"] = {
                p_id: [str(card) for card in cards]
                for p_id, cards in self.bidding_cards.items()
            }
        status["turn_player_id"] = self.bidding_turn_player_id
        
        # 添加当前轮次和上一轮出牌信息
        if hasattr(self, "current_trick_with_player"):
            status["current_trick"] = self.current_trick_with_player
        if hasattr(self, "last_trick"):
            status["last_trick"] = self.last_trick
        
        return status

    def _prepare_bidding_turn(self, acting_player: Player) -> None:
        """根据出价玩家设置反主顺序（从其下家开始）"""
        player_ids = self._players_in_order()
        if acting_player.id not in player_ids:
            self._bidding_queue = []
            self.bidding_turn_player_id = None
            return
        idx = player_ids.index(acting_player.id)
        queue = player_ids[idx + 1 :] + player_ids[:idx]
        queue = [pid for pid in queue if pid != acting_player.id]
        self._bidding_queue = queue
        self.bidding_turn_player_id = self._bidding_queue[0] if self._bidding_queue else None

    def _players_in_order(self) -> List[str]:
        result: List[str] = []
        for pos in self.dealing_order:
            player = self.get_player_by_position(pos)
            if player:
                result.append(player.id)
        return result
    
    def _calculate_trick_points_from_current_trick(self) -> int:
        """从current_trick_with_player计算当墩分数"""
        points = 0
        for entry in self.current_trick_with_player:
            for card_str in entry["cards"]:
                card = self._parse_card_string(card_str)
                if card and not card.is_joker:
                    if card.rank == Rank.FIVE:
                        points += 5
                    elif card.rank == Rank.TEN:
                        points += 10
                    elif card.rank == Rank.KING:
                        points += 10
        return points
    
    def _handle_game_end(self) -> None:
        """
        处理游戏结束逻辑：
        1. 确保最后一轮已处理（判断大小、扣底）
        2. 计算升级
        3. 确定下一轮庄家
        4. 进入scoring阶段
        """
        if self.game_phase != "playing":
            return
        
        # 确保最后一轮的分数已经计算（_handle_trick_completion已经处理）
        # 获取最终闲家得分（包括扣底）
        final_idle_score = self.idle_score
        
        # 获取扣底信息（已在_handle_bottom_bonus中计算并保存）
        bottom_score = 0
        bottom_bonus = 0
        if self.bottom_bonus_info:
            bottom_score = self.bottom_bonus_info["bottom_score"]
            bottom_bonus = self.bottom_bonus_info["bonus"]
        
        # 计算基础得分（不含扣底）
        # final_idle_score已经包含了扣底，所以需要减去扣底得到基础得分
        base_idle_score = final_idle_score - bottom_bonus
        
        # 计算升级
        # 升级规则：
        # 1. 闲家分数抹零（65分视作60分）
        # 2. 对于剩下的分数r：
        #    - 如果达到80，则闲家方升(r-80)//10级
        #    - 如果没有达到80，则庄家方升(80-r)//10级
        # 3. 庄家和闲家的级别是独立计算的
        
        # 确定当前庄家方和闲家方
        # 庄家方：NORTH-SOUTH 或 EAST-WEST（根据dealer_position）
        # 闲家方：另一方
        if self.dealer_position in [PlayerPosition.NORTH, PlayerPosition.SOUTH]:
            dealer_side = "north_south"
            idle_side = "east_west"
            dealer_level = self.north_south_level
            idle_level = self.east_west_level
        else:
            dealer_side = "east_west"
            idle_side = "north_south"
            dealer_level = self.east_west_level
            idle_level = self.north_south_level
        
        # 保存升级前的级别（用于round_summary）
        old_north_south_level = self.north_south_level
        old_east_west_level = self.east_west_level
        
        # 需求2：检查庄家是否在打A（级牌为14，即A）
        dealer_is_playing_ace = (dealer_level == 14)
        
        # 使用升级模块计算升级级数
        dealer_level_up, idle_level_up, rounded_score = calculate_level_up(
            final_idle_score=final_idle_score,
            dealer_level=dealer_level,
            level_up_mode=self.level_up_mode
        )
        
        # 应用升级（限制最大级别为14）
        dealer_level = min(14, dealer_level + dealer_level_up)
        idle_level = min(14, idle_level + idle_level_up)
        
        # 需求2：检查庄家是否胜利（打A且升级）
        dealer_wins = dealer_is_playing_ace and dealer_level_up > 0
        
        # 需求3：记录打A前的计数（用于前端显示）
        north_south_ace_count_before = self.north_south_ace_count
        east_west_ace_count_before = self.east_west_ace_count
        
        # 需求3：更新打A次数统计（仅在ace_reset_enabled时生效）
        dealer_penalty = False
        if self.ace_reset_enabled:
            if dealer_is_playing_ace:
                # 庄家在打A，增加计数
                if dealer_side == "north_south":
                    self.north_south_ace_count += 1
                else:
                    self.east_west_ace_count += 1
            
            # 需求3：检查是否需要惩罚（打A三次仍未胜利）
            if dealer_is_playing_ace and not dealer_wins:
                # 打A但未胜利，检查是否达到3次
                ace_count = self.north_south_ace_count if dealer_side == "north_south" else self.east_west_ace_count
                if ace_count >= 3:
                    # 达到3次，重置级别为2
                    dealer_level = 2
                    dealer_penalty = True
                    # 清零计数
                    if dealer_side == "north_south":
                        self.north_south_ace_count = 0
                    else:
                        self.east_west_ace_count = 0
            
            # 需求2：如果庄家胜利，清零打A计数（因为已经胜利）
            if dealer_wins:
                if dealer_side == "north_south":
                    self.north_south_ace_count = 0
                else:
                    self.east_west_ace_count = 0
        
        # 更新级别（根据位置）
        if dealer_side == "north_south":
            self.north_south_level = dealer_level
            self.east_west_level = idle_level
        else:
            self.east_west_level = dealer_level
            self.north_south_level = idle_level
        
        # 更新card_system的current_level为庄家级别（因为级牌以庄家级别为准）
        self.card_system.set_level(dealer_level)
        self.bidding_system = BiddingSystem(dealer_level)
        
        # 计算下一轮庄家
        next_dealer = self.calculate_next_dealer(final_idle_score)
        
        # 获取下一轮庄家玩家信息
        next_dealer_player = self.get_player_by_position(next_dealer)
        next_dealer_name = next_dealer_player.name if next_dealer_player else next_dealer.value
        
        # 确定胜利方信息（如果有胜利）
        winner_side = None
        winner_side_name = None
        if dealer_wins:
            winner_side = dealer_side
            if dealer_side == "north_south":
                winner_side_name = "南北方"
            else:
                winner_side_name = "东西方"
        
        # 保存本局总结信息（包括底牌，用于查看）
        self.round_summary = {
            "idle_score": base_idle_score,  # 基础得分（不含扣底）
            "bottom_score": bottom_score,
            "bottom_bonus": bottom_bonus,
            "total_score": final_idle_score,  # 总得分（包括扣底，完整分数，不抹零）
            "dealer_side": dealer_side,  # 当前庄家方："north_south" 或 "east_west"
            "idle_side": idle_side,  # 当前闲家方
            "dealer_level_up": dealer_level_up,
            "idle_level_up": idle_level_up,
            "old_north_south_level": old_north_south_level,
            "old_east_west_level": old_east_west_level,
            "new_north_south_level": self.north_south_level,
            "new_east_west_level": self.east_west_level,
            "next_dealer": next_dealer.value,
            "next_dealer_name": next_dealer_name,
            "bottom_cards": [str(card) for card in self.bottom_cards],  # 保存底牌字符串列表
            "tricks_won": self.tricks_won.copy(),
            "dealer_wins": dealer_wins,  # 需求2：庄家是否胜利
            "winner_side": winner_side,  # 胜利方："north_south" 或 "east_west"，无胜利时为None
            "winner_side_name": winner_side_name,  # 胜利方名称："南北方" 或 "东西方"，无胜利时为None
            "dealer_penalty": dealer_penalty,  # 需求3：庄家是否被惩罚
            "north_south_ace_count": self.north_south_ace_count,  # 需求3：南北方打A次数（当前）
            "east_west_ace_count": self.east_west_ace_count,  # 需求3：东西方打A次数（当前）
            "north_south_ace_count_before": north_south_ace_count_before,  # 需求3：南北方打A次数（本轮前）
            "east_west_ace_count_before": east_west_ace_count_before,  # 需求3：东西方打A次数（本轮前）
            "dealer_is_playing_ace": dealer_is_playing_ace  # 需求3：本轮庄家是否在打A
        }
        
        # 进入scoring阶段
        self.game_phase = "scoring"
        # 清空ready状态
        self.players_ready_for_next_round = set()
        # 注意：不清空players_ready_to_start，因为下一轮开始时需要重新准备
    
    def ready_to_start_game(self, player_id: str) -> Dict[str, Any]:
        """
        玩家准备开始游戏（waiting阶段使用）
        
        Args:
            player_id: 玩家ID
            
        Returns:
            包含是否所有玩家都ready的信息，如果都ready则自动开始游戏
        """
        if self.game_phase != "waiting":
            return {"success": False, "message": "当前不在等待阶段"}
        
        # 验证玩家是否在房间中
        player = self.get_player_by_id(player_id)
        if not player:
            return {"success": False, "message": "玩家不存在"}
        
        # 添加玩家到ready集合
        self.players_ready_to_start.add(player_id)
        
        # 检查是否所有玩家都ready
        all_ready = len(self.players_ready_to_start) == len(self.room.players) and len(self.room.players) == 4
        
        # 如果所有玩家都ready，自动开始游戏
        if all_ready:
            if self.start_game():
                return {
                    "success": True,
                    "all_ready": True,
                    "ready_count": len(self.players_ready_to_start),
                    "total_players": len(self.room.players),
                    "ready_players": list(self.players_ready_to_start),
                    "game_started": True
                }
            else:
                return {"success": False, "message": "无法开始游戏"}
        
        return {
            "success": True,
            "all_ready": False,
            "ready_count": len(self.players_ready_to_start),
            "total_players": len(self.room.players),
            "ready_players": list(self.players_ready_to_start),
            "game_started": False
        }
    
    def cancel_ready_to_start_game(self, player_id: str) -> Dict[str, Any]:
        """
        玩家取消准备开始游戏（waiting阶段使用）
        
        Args:
            player_id: 玩家ID
            
        Returns:
            包含取消准备后的状态信息
        """
        if self.game_phase != "waiting":
            return {"success": False, "message": "当前不在等待阶段"}
        
        # 验证玩家是否在房间中
        player = self.get_player_by_id(player_id)
        if not player:
            return {"success": False, "message": "玩家不存在"}
        
        # 从ready集合中移除玩家
        self.players_ready_to_start.discard(player_id)
        
        return {
            "success": True,
            "ready_count": len(self.players_ready_to_start),
            "total_players": len(self.room.players),
            "ready_players": list(self.players_ready_to_start)
        }
    
    def ready_for_next_round(self, player_id: str) -> Dict[str, Any]:
        """
        玩家准备进入下一轮
        
        Args:
            player_id: 玩家ID
            
        Returns:
            包含是否所有玩家都ready的信息
        """
        if self.game_phase != "scoring":
            return {"success": False, "message": "当前不在计分阶段"}
        
        # 验证玩家是否在房间中
        player = self.get_player_by_id(player_id)
        if not player:
            return {"success": False, "message": "玩家不存在"}
        
        # 添加玩家到ready集合
        self.players_ready_for_next_round.add(player_id)
        
        # 检查是否所有玩家都ready
        all_ready = len(self.players_ready_for_next_round) == len(self.room.players)
        
        return {
            "success": True,
            "all_ready": all_ready,
            "ready_count": len(self.players_ready_for_next_round),
            "total_players": len(self.room.players),
            "ready_players": list(self.players_ready_for_next_round)  # 包含所有已准备玩家的ID列表
        }
    
    def start_next_round(self) -> bool:
        """
        开始下一轮游戏（当所有玩家都准备好时自动调用）
        
        Returns:
            是否成功开始
        """
        if self.game_phase != "scoring":
            return False
        
        if len(self.players_ready_for_next_round) != len(self.room.players):
            return False
        
        # 需求2：检查庄家是否胜利，如果胜利则重置游戏
        dealer_wins = self.round_summary.get("dealer_wins", False) if self.round_summary else False
        
        if dealer_wins:
            # 庄家胜利，重置游戏到初始状态
            # 重置级别为2
            self.north_south_level = 2
            self.east_west_level = 2
            # 重置打A次数
            self.north_south_ace_count = 0
            self.east_west_ace_count = 0
            # 重置为初始状态（从级牌2重新开始，进入第一局游戏状态）
            self.is_first_round = True
            # 清空定主方（重新开始时需要重新确定定主方）
            self.fixed_dealer_position = None
            # 清空round_summary
            self.round_summary = None
            # 调用end_round来重置状态
            self.end_round(self.idle_score)
            return True
        
        # 应用下一轮设置
        if self.round_summary:
            self.dealer_position = PlayerPosition(self.round_summary["next_dealer"])
            # 如果这是第一局，固定庄家位置
            if self.is_first_round:
                self.fixed_dealer_position = self.dealer_position
        
        # 直接开始下一轮游戏（不等待玩家再次准备）
        # 注意：这里不检查players_ready_to_start，因为所有玩家已经通过ready_for_next_round准备好了
        if self.fixed_dealer_position is not None:
            self.dealer_position = self.fixed_dealer_position
        
        # 根据新的庄家位置确定对应的级别，并更新card_system和bidding_system
        if self.dealer_position in [PlayerPosition.NORTH, PlayerPosition.SOUTH]:
            new_dealer_level = self.north_south_level
        else:
            new_dealer_level = self.east_west_level
        
        # 更新card_system的current_level为新庄家级别（因为级牌以庄家级别为准）
        self.card_system.set_level(new_dealer_level)
        # 更新bidding_system使用新庄家级别
        self.bidding_system = BiddingSystem(new_dealer_level)
        
        # 重置一轮游戏的状态
        self._reset_round_state()
        
        # 创建并洗牌
        deck = self.card_system.create_deck()
        self.card_system.shuffle_deck()
        
        # 前100张作为发牌区，后8张作为底牌
        self.dealing_deck = deck[0:100]
        self.bottom_cards = deck[100:108]
        
        # 清空玩家手牌
        for p in self.room.players:
            p.cards = []
        
        # 发牌顺序：从庄家开始
        self._set_dealing_order_from_dealer()
        
        self.dealt_count = 0
        
        return True
    
    def _parse_card_string(self, card_str: str) -> Optional[Card]:
        """解析卡牌字符串为Card对象"""
        try:
            if "JOKER-A" in card_str or "JOKER/大王" in card_str:
                return Card(rank=Rank.BIG_JOKER, is_joker=True)
            elif "JOKER-B" in card_str or "JOKER/小王" in card_str:
                return Card(rank=Rank.SMALL_JOKER, is_joker=True)
            else:
                suit_map = {"♠": Suit.SPADES, "♥": Suit.HEARTS, "♣": Suit.CLUBS, "♦": Suit.DIAMONDS}
                suit_char = card_str[-1]
                rank_str = card_str[:-1]
                suit = suit_map.get(suit_char)
                rank = Rank(rank_str)
                return Card(rank=rank, suit=suit)
        except:
            return None
    
    def _determine_trick_winner(self, result) -> Optional[PlayerPosition]:
        """
        确定一轮的获胜者
        直接使用已经比较好的current_trick_max_player_id，不需要重新计算
        
        Args:
            result: CardPlayingSystem返回的PlayResult
            
        Returns:
            获胜者的位置，如果无法确定则返回None
        """
        if self.current_trick_max_player_id:
            winner_player = self.get_player_by_id(self.current_trick_max_player_id)
            if winner_player:
                return winner_player.position
        
        # 兜底：如果current_trick_max_player_id未设置或找不到玩家，使用result.winner或trick_leader
        return result.winner if result.winner else self.trick_leader
    
    def _handle_trick_completion(self, winner: PlayerPosition) -> None:
        """
        处理一轮完成后的所有逻辑
        
        Args:
            winner: 获胜者的位置
        """
        self._update_tricks_won(winner)
        self._calculate_and_update_score(winner)
        self._update_next_round_leader(winner)
        self._save_and_reset_trick()
    
    def _update_tricks_won(self, winner: PlayerPosition) -> None:
        """更新获胜墩数"""
        if winner in [PlayerPosition.NORTH, PlayerPosition.SOUTH]:
            self.tricks_won["north_south"] += 1
        else:
            self.tricks_won["east_west"] += 1
    
    def _calculate_and_update_score(self, winner: PlayerPosition) -> None:
        """计算并更新分数"""
        if not self.card_playing_system:
            return
        
        # 设置expected_leader为下一轮的领出者
        self.card_playing_system.expected_leader = winner
        
        # 计算当墩分数
        trick_points = self._calculate_trick_points_from_current_trick()
        if winner in self.card_playing_system.idle_positions:
            self.card_playing_system.idle_score += trick_points
            # 处理抠底机制
            self._handle_bottom_bonus(winner)
        
        # 更新分数：从CardPlayingSystem获取闲家累计分数
        self.idle_score = self.card_playing_system.get_idle_score()
    
    def _handle_bottom_bonus(self, winner: PlayerPosition) -> None:
        """
        处理抠底机制，只发生在最后一墩
        
        Args:
            winner: 获胜者的位置
        """
        all_hands_empty = all(len(p.cards) == 0 for p in self.room.players)
        if not all_hands_empty or not self.card_playing_system.bottom_cards:
            self.bottom_bonus_info = None  # 没有扣底
            return
        
        # 检查是否是闲家获胜
        if winner not in self.card_playing_system.idle_positions:
            self.bottom_bonus_info = None  # 庄家获胜，没有扣底
            return
        
        bottom_score = sum(self.card_system.get_card_score(card) 
                         for card in self.card_playing_system.bottom_cards)
        
        # 使用领出者的牌型判断倍率
        # 注意：必须在_save_and_reset_trick之前获取，因为_save_and_reset_trick可能会清空current_trick_with_player
        led_cards = self._get_led_cards_from_current_trick()
        if led_cards:
            multiplier = self.card_playing_system._get_last_trick_multiplier(led_cards)
            bonus = bottom_score * multiplier
            self.card_playing_system.idle_score += bonus
            # 保存扣底信息用于展示
            self.bottom_bonus_info = {
                "bottom_score": bottom_score,
                "multiplier": multiplier,
                "bonus": bonus
            }
            print(f"[抠底] 闲家赢，底牌分：{bottom_score}，倍数：{multiplier}，抠底得分：+{bonus}")
        else:
            self.bottom_bonus_info = None
    
    def _get_led_cards_from_current_trick(self) -> List[Card]:
        """从current_trick_with_player获取领出者的牌"""
        if not self.current_trick_with_player:
            return []
        
        led_entry = self.current_trick_with_player[0]
        led_cards = []
        for card_str in led_entry["cards"]:
            parsed = self._parse_card_string(card_str)
            if parsed:
                led_cards.append(parsed)
        return led_cards
    
    def _update_next_round_leader(self, winner: PlayerPosition) -> None:
        """更新下一轮的领出者"""
        self.current_player = winner
        # 更新当前玩家ID
        winner_player = self.get_player_by_position(winner)
        self.current_player_id = winner_player.id if winner_player else None
    
    def _save_and_reset_trick(self) -> None:
        """保存上一轮出牌信息并重置当前轮次状态"""
        # 保存上一轮出牌信息（在清空之前保存，用于前端延迟显示）
        self.last_trick = self.current_trick_with_player.copy()
        # 清空当前轮次（为下一轮准备）
        # 注意：前端会延迟2秒清空显示，但后端需要立即清空以便下一轮使用
        self.current_trick = []
        # 注意：保留current_trick_with_player，让前端在trick_complete事件中获取
        # 在websocket处理完trick_complete事件后再清空
        # self.current_trick_with_player = []  # 延迟清空，在websocket中处理
        self.trick_leader = None
        self.current_trick_max_player_id = None  # 清空当前轮次最大玩家
    
