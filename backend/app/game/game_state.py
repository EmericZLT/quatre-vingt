"""
八十分游戏状态管理
"""
from typing import List, Optional, Dict, Any
from datetime import datetime
from app.models.game import GameRoom, Player, PlayerPosition, GameStatus, Suit, Card
from app.game.card_system import CardSystem
from app.game.bidding_system import BiddingSystem


class GameState:
    """游戏状态管理类"""
    
    def __init__(self, room: GameRoom):
        self.room = room
        self.card_system = CardSystem()
        self.bidding_system = BiddingSystem(self.card_system.current_level)
        self.trump_suit: Optional[Suit] = None
        self.dealer_position: PlayerPosition = PlayerPosition.NORTH
        self.current_player: PlayerPosition = PlayerPosition.NORTH
        self.current_trick: List[Card] = []
        self.trick_leader: Optional[PlayerPosition] = None
        self.game_phase = "waiting"  # waiting, dealing, bidding, playing, scoring
        self.scores = {"north_south": 0, "east_west": 0}
        self.tricks_won = {"north_south": 0, "east_west": 0}
        self.bottom_cards: List[Card] = []  # 底牌，始终8张
        self.dealer_has_bottom = False  # 庄家是否已获得底牌
        
    def start_game(self) -> bool:
        """开始游戏"""
        if not self.room.can_start:
            return False
        
        self.room.status = GameStatus.PLAYING
        self.game_phase = "dealing"
        
        # 创建并洗牌
        self.card_system.create_deck()
        self.card_system.shuffle_deck()
        
        # 发牌
        hands = self.card_system.deal_cards()
        
        # 给每个玩家发牌（每人25张）
        for player in self.room.players:
            position = player.position.value
            player.cards = hands[position]
        
        # 设置底牌（8张，不属于任何玩家）
        self.bottom_cards = hands['bottom']
        
        self.game_phase = "bidding"
        return True
    
    def set_trump_suit(self, suit: Suit) -> bool:
        """设置主牌花色"""
        if self.game_phase != "bidding":
            return False
        
        self.trump_suit = suit
        self.room.trump_suit = suit
        
        # 庄家获得底牌
        self.give_bottom_to_dealer()
        
        self.game_phase = "playing"
        return True
    
    def give_bottom_to_dealer(self) -> bool:
        """庄家获得底牌"""
        if self.dealer_has_bottom:
            return False
        
        dealer = self.get_dealer()
        if not dealer:
            return False
        
        # 庄家获得底牌（33张牌）
        dealer.cards.extend(self.bottom_cards)
        self.dealer_has_bottom = True
        return True
    
    def dealer_discard_bottom(self, cards_to_discard: List[Card]) -> bool:
        """庄家扣底（从手中扣出8张牌作为新底牌）"""
        if not self.dealer_has_bottom:
            return False
        
        dealer = self.get_dealer()
        if not dealer:
            return False
        
        # 检查庄家是否有这些牌
        for card in cards_to_discard:
            if card not in dealer.cards:
                return False
        
        # 移除庄家手中的牌
        for card in cards_to_discard:
            dealer.cards.remove(card)
        
        # 设置新的底牌
        self.bottom_cards = cards_to_discard
        return True
    
    def get_dealer(self) -> Optional[Player]:
        """获取庄家"""
        return self.get_player_by_position(self.dealer_position)
    
    def make_bid(self, player_id: str, cards: List[Card]) -> Dict[str, Any]:
        """玩家亮主"""
        if self.game_phase != "bidding":
            return {"success": False, "message": "当前不是亮主阶段"}
        
        # 检查玩家是否有这些牌
        player = self.get_player_by_id(player_id)
        if not player:
            return {"success": False, "message": "玩家不存在"}
        
        for card in cards:
            if card not in player.cards:
                return {"success": False, "message": "玩家没有这些牌"}
        
        # 调用亮主系统
        result = self.bidding_system.make_bid(player_id, cards)
        
        if result["success"]:
            # 从玩家手中移除亮主的牌
            for card in cards:
                player.cards.remove(card)
        
        return result
    
    def finish_bidding(self) -> bool:
        """结束亮主阶段"""
        if self.game_phase != "bidding":
            return False
        
        # 结束亮主
        final_bid = self.bidding_system.finish_bidding()
        
        if final_bid:
            # 设置主牌花色
            self.trump_suit = self.bidding_system.get_trump_suit()
            self.room.trump_suit = self.trump_suit
            
            # 庄家获得底牌
            self.give_bottom_to_dealer()
            
            self.game_phase = "playing"
            return True
        else:
            # 无人亮主，翻底牌确定主牌
            return self._determine_trump_from_bottom()
    
    def _determine_trump_from_bottom(self) -> bool:
        """从底牌确定主牌花色"""
        if not self.bottom_cards:
            return False
        
        # 简化版本：选择底牌中第一张非王牌的花色
        for card in self.bottom_cards:
            if not card.is_joker:
                self.trump_suit = card.suit
                self.room.trump_suit = self.trump_suit
                self.give_bottom_to_dealer()
                self.game_phase = "playing"
                return True
        
        # 如果底牌全是王牌，设为无主
        self.trump_suit = None
        self.room.trump_suit = None
        self.give_bottom_to_dealer()
        self.game_phase = "playing"
        return True
    
    def get_bidding_status(self) -> Dict[str, Any]:
        """获取亮主状态"""
        return self.bidding_system.get_bidding_status()
    
    def play_card(self, player_id: str, card: Card) -> bool:
        """玩家出牌"""
        if self.game_phase != "playing":
            return False
        
        # 找到出牌玩家
        player = self.get_player_by_id(player_id)
        if not player:
            return False
        
        # 检查玩家是否有这张牌
        if card not in player.cards:
            return False
        
        # 移除玩家手中的牌
        player.cards.remove(card)
        
        # 添加到当前圈
        self.current_trick.append(card)
        
        # 如果是第一张牌，记录领出者
        if len(self.current_trick) == 1:
            self.trick_leader = player.position
        
        # 如果一圈出完，判断获胜者
        if len(self.current_trick) == 4:
            winner = self.determine_trick_winner()
            self.tricks_won[winner] += 1
            self.current_trick = []
            self.trick_leader = None
        
        return True
    
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
    
    def calculate_scores(self) -> Dict[str, int]:
        """计算得分"""
        # 简化版本：返回当前得分
        return self.scores.copy()
    
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
            "current_level": self.card_system.current_level,
            "trump_suit": self.trump_suit.value if self.trump_suit else None,
            "current_player": self.current_player.value,
            "dealer_position": self.dealer_position.value,
            "dealer_has_bottom": self.dealer_has_bottom,
            "bottom_cards_count": len(self.bottom_cards),
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
            "scores": self.scores,
            "tricks_won": self.tricks_won
        }
        
        # 添加亮主状态
        if self.game_phase == "bidding":
            status["bidding"] = self.get_bidding_status()
        
        return status
