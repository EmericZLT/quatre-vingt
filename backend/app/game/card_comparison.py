"""
牌大小比较逻辑
"""
from typing import List, Optional
from app.models.game import Card, Suit, Rank, PlayerPosition
from app.game.card_system import CardSystem


class CardComparison:
    """牌大小比较系统"""
    
    def __init__(self, card_system: CardSystem, trump_suit: Optional[Suit] = None):
        self.card_system = card_system
        self.trump_suit = trump_suit
    
    @property
    def current_level(self) -> int:
        """获取当前级别（从card_system动态获取，确保使用最新级别）"""
        return self.card_system.current_level
    
    def _get_level_rank(self) -> Rank:
        """获取当前级别的牌面"""
        level_ranks = {
            2: Rank.TWO, 3: Rank.THREE, 4: Rank.FOUR, 5: Rank.FIVE,
            6: Rank.SIX, 7: Rank.SEVEN, 8: Rank.EIGHT, 9: Rank.NINE,
            10: Rank.TEN, 11: Rank.JACK, 12: Rank.QUEEN, 13: Rank.KING, 14: Rank.ACE
        }
        return level_ranks[self.current_level]
    
    def compare_cards(self, card1: Card, card2: Card) -> int:
        """
        比较两张牌的大小
        返回: -1 (card1 < card2), 0 (card1 == card2), 1 (card1 > card2)
        """
        # 检查是否为同一张牌
        if card1.suit == card2.suit and card1.rank == card2.rank:
            return 0
        
        # 获取牌的大小值
        value1 = self._get_card_value(card1)
        value2 = self._get_card_value(card2)
        
        if value1 < value2:
            return -1
        elif value1 > value2:
            return 1
        else:
            return 0
    
    def _get_card_value(self, card: Card) -> int:
        """获取牌的大小值（用于比较）"""
        # 大小王最大
        if card.is_joker:
            if card.rank == Rank.BIG_JOKER:
                return 1000  # 大王最大
            elif card.rank == Rank.SMALL_JOKER:
                return 999   # 小王次之
        
        # 主牌
        if self._is_trump_card(card):
            return self._get_trump_value(card)
        
        # 副牌
        return self._get_side_value(card)
    
    def _is_trump_card(self, card: Card) -> bool:
        """检查是否为主牌"""
        # 大小王是主牌
        if card.is_joker:
            return True
        
        # 级牌是主牌
        if card.rank == self._get_level_rank():
            return True
        
        # 主牌花色的牌是主牌
        if self.trump_suit and card.suit == self.trump_suit:
            return True
        
        return False
    
    def _get_trump_value(self, card: Card) -> int:
        """获取主牌的大小值"""
        # 大小王
        if card.is_joker:
            if card.rank == Rank.BIG_JOKER:
                return 1000
            elif card.rank == Rank.SMALL_JOKER:
                return 999
        
        # 级牌（主牌中最大，除大小王外）
        if card.rank == self._get_level_rank():
            # 主级牌：花色和主牌花色一致的级牌（无主时没有主级牌）
            if self.trump_suit and card.suit == self.trump_suit:
                # 主级牌：返回更高的值
                return 950 + self._get_rank_value(card.rank)
            else:
                # 副级牌：所有副级牌彼此一样大，返回固定值
                return 900
        
        # 主牌花色的其他牌
        if self.trump_suit and card.suit == self.trump_suit:
            return 700 + self._get_rank_value(card.rank)
        
        return 0
    
    def _get_side_value(self, card: Card) -> int:
        """获取副牌的大小值"""
        return self._get_rank_value(card.rank)
    
    def _get_rank_value(self, rank: Rank) -> int:
        """获取牌面值"""
        rank_values = {
            Rank.TWO: 2, Rank.THREE: 3, Rank.FOUR: 4, Rank.FIVE: 5,
            Rank.SIX: 6, Rank.SEVEN: 7, Rank.EIGHT: 8, Rank.NINE: 9,
            Rank.TEN: 10, Rank.JACK: 11, Rank.QUEEN: 12, Rank.KING: 13, Rank.ACE: 14
        }
        return rank_values.get(rank, 0)
    
    def find_winner_card(self, cards: List[Card]) -> Card:
        """在一组牌中找到最大的牌"""
        if not cards:
            raise ValueError("Cannot find winner in empty list")
        
        winner = cards[0]
        for card in cards[1:]:
            if self.compare_cards(card, winner) > 0:
                winner = card
        
        return winner
    
    def compare_card_combinations(self, cards1: List[Card], cards2: List[Card]) -> int:
        """
        比较两组牌的大小
        返回: -1 (cards1 < cards2), 0 (cards1 == cards2), 1 (cards1 > cards2)
        """
        # 简化版本：比较最大牌
        if not cards1 or not cards2:
            return 0
        
        max_card1 = self.find_winner_card(cards1)
        max_card2 = self.find_winner_card(cards2)
        
        return self.compare_cards(max_card1, max_card2)
    
    def get_card_rank_info(self, card: Card) -> dict:
        """获取牌的等级信息"""
        return {
            "card": str(card),
            "is_trump": self._is_trump_card(card),
            "is_joker": card.is_joker,
            "is_level_card": card.rank == self._get_level_rank(),
            "is_trump_suit": self.trump_suit and card.suit == self.trump_suit,
            "value": self._get_card_value(card)
        }
