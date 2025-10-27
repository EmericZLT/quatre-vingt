"""
将吃（毙牌）逻辑系统
"""
from typing import List, Optional, Dict, Any
from app.models.game import Card, Suit, Rank, PlayerPosition
from app.game.card_comparison import CardComparison
from app.game.tractor_logic import TractorLogic


class TrumpLogic:
    """将吃逻辑处理"""
    
    def __init__(self, card_comparison: CardComparison, tractor_logic: TractorLogic):
        self.card_comparison = card_comparison
        self.tractor_logic = tractor_logic
        self.trump_suit = card_comparison.trump_suit
        self.current_level = card_comparison.current_level
    
    def can_trump(self, player_cards: List[Card], led_suit: Suit, led_card_type: str) -> bool:
        """检查玩家是否可以将吃"""
        # 检查手中是否有该花色的牌
        has_led_suit = any(card.suit == led_suit for card in player_cards)
        
        if has_led_suit:
            return False  # 有该花色不能将吃
        
        # 检查是否有足够的主牌来将吃
        trump_cards = [card for card in player_cards if self._is_trump_card(card)]
        
        if not trump_cards:
            return False  # 没有主牌不能将吃
        
        # 检查牌型匹配
        return self._can_match_card_type(trump_cards, led_card_type)
    
    def _is_trump_card(self, card: Card) -> bool:
        """检查是否为主牌"""
        # 大小王是主牌
        if card.is_joker:
            return True
        
        # 级牌是主牌
        if card.rank == self.card_comparison.level_rank:
            return True
        
        # 主牌花色的牌是主牌
        if self.trump_suit and card.suit == self.trump_suit:
            return True
        
        return False
    
    def _can_match_card_type(self, trump_cards: List[Card], led_card_type: str) -> bool:
        """检查主牌是否能匹配牌型"""
        if led_card_type == "single":
            return len(trump_cards) >= 1
        elif led_card_type == "pair":
            return self._has_pair(trump_cards)
        elif led_card_type == "tractor":
            return self.tractor_logic.is_tractor(trump_cards)
        elif led_card_type == "slingshot":
            return self._can_slingshot(trump_cards)
        
        return False
    
    def _has_pair(self, cards: List[Card]) -> bool:
        """检查是否有对子"""
        if len(cards) < 2:
            return False
        
        # 按牌面分组
        rank_groups = {}
        for card in cards:
            if card.rank not in rank_groups:
                rank_groups[card.rank] = []
            rank_groups[card.rank].append(card)
        
        # 检查是否有对子
        for rank, rank_cards in rank_groups.items():
            if len(rank_cards) >= 2:
                return True
        
        return False
    
    def _can_slingshot(self, cards: List[Card]) -> bool:
        """检查是否可以甩牌"""
        if len(cards) < 2:
            return False
        
        # 检查是否为同一花色
        first_suit = cards[0].suit
        return all(card.suit == first_suit for card in cards)
    
    def get_trump_options(self, player_cards: List[Card], led_suit: Suit, led_card_type: str) -> List[Card]:
        """获取可用的将吃选项"""
        if not self.can_trump(player_cards, led_suit, led_card_type):
            return []
        
        trump_cards = [card for card in player_cards if self._is_trump_card(card)]
        
        if led_card_type == "single":
            return trump_cards
        elif led_card_type == "pair":
            return self._get_pair_options(trump_cards)
        elif led_card_type == "tractor":
            return self._get_tractor_options(trump_cards)
        elif led_card_type == "slingshot":
            return self._get_slingshot_options(trump_cards)
        
        return []
    
    def _get_pair_options(self, trump_cards: List[Card]) -> List[Card]:
        """获取对子选项"""
        # 简化版本：返回所有主牌
        return trump_cards
    
    def _get_tractor_options(self, trump_cards: List[Card]) -> List[Card]:
        """获取拖拉机选项"""
        # 简化版本：返回所有主牌
        return trump_cards
    
    def _get_slingshot_options(self, trump_cards: List[Card]) -> List[Card]:
        """获取甩牌选项"""
        # 简化版本：返回所有主牌
        return trump_cards
    
    def can_over_trump(self, current_trump_card: Card, new_trump_card: Card) -> bool:
        """检查是否可以超将吃"""
        # 使用比大小逻辑判断
        return self.card_comparison.compare_cards(new_trump_card, current_trump_card) > 0
    
    def get_trump_info(self, player_cards: List[Card], led_suit: Suit, led_card_type: str) -> Dict[str, Any]:
        """获取将吃信息"""
        can_trump = self.can_trump(player_cards, led_suit, led_card_type)
        trump_options = self.get_trump_options(player_cards, led_suit, led_card_type)
        
        return {
            "can_trump": can_trump,
            "trump_options_count": len(trump_options),
            "trump_options": [str(card) for card in trump_options],
            "led_suit": led_suit.value if led_suit else None,
            "led_card_type": led_card_type
        }


