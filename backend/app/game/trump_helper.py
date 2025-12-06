"""
主副牌判断辅助工具
集中处理所有与主副牌判断相关的逻辑
"""
from typing import Optional
from app.models.game import Card, Suit, Rank
from app.game.card_system import CardSystem


class TrumpHelper:
    """
    主副牌判断辅助类
    
    职责：
    1. 判断一张牌是否为主牌
    2. 获取一张牌的花色类型（"trump" 或具体花色值）
    3. 判断多张牌是否为同一花色类型
    
    这个类是无状态的工具类，所有方法都基于传入的参数进行判断
    """
    
    def __init__(self, card_system: CardSystem, trump_suit: Optional[Suit] = None):
        """
        初始化主副牌判断辅助类
        
        Args:
            card_system: 卡牌系统（用于获取当前级别）
            trump_suit: 主牌花色（如果已定主）
        """
        self.card_system = card_system
        self.trump_suit = trump_suit
    
    def is_trump(self, card: Card) -> bool:
        """
        判断一张牌是否为主牌
        
        主牌包括：
        1. 大小王
        2. 级牌（当前级别对应的牌面）
        3. 主牌花色的牌
        
        Args:
            card: 要判断的牌
            
        Returns:
            True: 是主牌
            False: 不是主牌（副牌）
        """
        # 大小王是主牌
        if card.is_joker:
            return True
        
        # 级牌是主牌
        if card.rank == self.card_system.get_level_rank():
            return True
        
        # 主牌花色的牌是主牌
        if self.trump_suit and card.suit == self.trump_suit:
            return True
        
        return False
    
    def get_card_suit(self, card: Card) -> Optional[str]:
        """
        获取牌的花色类型
        
        这个方法将牌分类为：
        - "trump": 主牌（包括大小王、级牌、主牌花色）
        - 具体花色值: 副牌花色（如 "♠", "♥", "♦", "♣"）
        
        Args:
            card: 要判断的牌
            
        Returns:
            "trump": 主牌
            具体花色值: 副牌花色
            None: 理论上不会出现（除非牌的数据有问题）
        """
        # 大小王
        if card.rank in [Rank.SMALL_JOKER, Rank.BIG_JOKER]:
            return "trump"
        
        # 级牌（使用 CardSystem 的方法判断）
        if card.rank == self.card_system.get_level_rank():
            return "trump"
        
        # 主牌花色
        if self.trump_suit and card.suit == self.trump_suit:
            return "trump"
        
        # 副牌
        return card.suit.value if card.suit else None
    
    def is_same_suit(self, card1: Card, card2: Card) -> bool:
        """
        判断两张牌是否为同一花色类型
        
        Args:
            card1: 第一张牌
            card2: 第二张牌
            
        Returns:
            True: 同一花色类型
            False: 不同花色类型
        """
        return self.get_card_suit(card1) == self.get_card_suit(card2)
    
    def are_all_same_suit(self, cards: list[Card]) -> bool:
        """
        判断多张牌是否都是同一花色类型
        
        Args:
            cards: 牌列表
            
        Returns:
            True: 所有牌都是同一花色类型
            False: 有不同花色类型的牌
        """
        if not cards:
            return True
        
        first_suit = self.get_card_suit(cards[0])
        return all(self.get_card_suit(c) == first_suit for c in cards)
    
    def filter_by_suit(self, cards: list[Card], suit_type: str) -> list[Card]:
        """
        筛选出指定花色类型的牌
        
        Args:
            cards: 牌列表
            suit_type: 花色类型（"trump" 或具体花色值）
            
        Returns:
            指定花色类型的牌列表
        """
        return [c for c in cards if self.get_card_suit(c) == suit_type]
    
    def count_by_suit(self, cards: list[Card], suit_type: str) -> int:
        """
        统计指定花色类型的牌数量
        
        Args:
            cards: 牌列表
            suit_type: 花色类型（"trump" 或具体花色值）
            
        Returns:
            指定花色类型的牌数量
        """
        return len(self.filter_by_suit(cards, suit_type))

