"""
八十分纸牌系统
"""
import random
from typing import List, Optional
from app.models.game import Card, Suit, Rank


class CardSystem:
    """纸牌系统类"""
    
    def __init__(self):
        self.deck: List[Card] = []
        self.current_level: int = 2  # 当前级别，从2开始
    
    def create_deck(self) -> List[Card]:
        """创建两副扑克牌（108张）"""
        self.deck = []
        
        # 创建两副牌
        for _ in range(2):
            # 添加普通牌（2-A）
            for suit in Suit:
                for rank in Rank:
                    self.deck.append(Card(suit=suit, rank=rank))
            
            # 添加大小王
            self.deck.append(Card(suit=Suit.SPADES, rank=Rank.ACE, is_joker=True))  # 大王
            self.deck.append(Card(suit=Suit.HEARTS, rank=Rank.ACE, is_joker=True))  # 小王
        
        return self.deck
    
    def shuffle_deck(self) -> List[Card]:
        """洗牌"""
        random.shuffle(self.deck)
        return self.deck
    
    def deal_cards(self) -> dict:
        """发牌：每人25张，留8张底牌"""
        if len(self.deck) != 108:
            raise ValueError("牌数不正确，应该是108张")
        
        # 每人25张，4人共100张，剩余8张作为底牌
        hands = {
            'north': self.deck[0:25],
            'east': self.deck[25:50],
            'south': self.deck[50:75],
            'west': self.deck[75:100],
            'bottom': self.deck[100:108]  # 底牌
        }
        
        return hands
    
    def get_card_value(self, card: Card, trump_suit: Optional[Suit] = None) -> int:
        """获取纸牌大小值（用于比较）"""
        if card.is_joker:
            # 大小王
            if card.suit == Suit.SPADES:  # 大王
                return 1000
            else:  # 小王
                return 999
        
        # 普通牌的大小值
        rank_values = {
            Rank.TWO: 2, Rank.THREE: 3, Rank.FOUR: 4, Rank.FIVE: 5,
            Rank.SIX: 6, Rank.SEVEN: 7, Rank.EIGHT: 8, Rank.NINE: 9,
            Rank.TEN: 10, Rank.JACK: 11, Rank.QUEEN: 12, Rank.KING: 13, Rank.ACE: 14
        }
        
        base_value = rank_values[card.rank]
        
        # 如果是主牌，增加权重
        if trump_suit and card.suit == trump_suit:
            base_value += 100  # 主牌比副牌大
        
        # 如果是级牌，增加更多权重
        if self.is_level_card(card):
            base_value += 200  # 级牌最大（除大小王外）
        
        return base_value
    
    def is_level_card(self, card: Card) -> bool:
        """判断是否为级牌"""
        if card.is_joker:
            return False
        
        # 根据当前级别判断
        level_ranks = {
            2: Rank.TWO, 3: Rank.THREE, 4: Rank.FOUR, 5: Rank.FIVE,
            6: Rank.SIX, 7: Rank.SEVEN, 8: Rank.EIGHT, 9: Rank.NINE,
            10: Rank.TEN, 11: Rank.JACK, 12: Rank.QUEEN, 13: Rank.KING, 14: Rank.ACE
        }
        
        return card.rank == level_ranks.get(self.current_level)
    
    def get_card_score(self, card: Card) -> int:
        """获取纸牌分数（5=5分，10和K=10分）"""
        if card.is_joker:
            return 0
        
        if card.rank == Rank.FIVE:
            return 5
        elif card.rank in [Rank.TEN, Rank.KING]:
            return 10
        else:
            return 0
    
    def compare_cards(self, card1: Card, card2: Card, trump_suit: Optional[Suit] = None) -> int:
        """比较两张牌的大小，返回1(card1大)、-1(card2大)、0(相等)"""
        value1 = self.get_card_value(card1, trump_suit)
        value2 = self.get_card_value(card2, trump_suit)
        
        if value1 > value2:
            return 1
        elif value1 < value2:
            return -1
        else:
            return 0
    
    def set_level(self, level: int):
        """设置当前级别"""
        if 2 <= level <= 14:
            self.current_level = level
        else:
            raise ValueError("级别必须在2-14之间")
    
    def get_level_rank(self) -> Rank:
        """获取当前级别的牌面"""
        level_ranks = {
            2: Rank.TWO, 3: Rank.THREE, 4: Rank.FOUR, 5: Rank.FIVE,
            6: Rank.SIX, 7: Rank.SEVEN, 8: Rank.EIGHT, 9: Rank.NINE,
            10: Rank.TEN, 11: Rank.JACK, 12: Rank.QUEEN, 13: Rank.KING, 14: Rank.ACE
        }
        return level_ranks[self.current_level]
