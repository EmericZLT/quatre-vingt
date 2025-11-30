"""
八十分亮主和反主系统
"""
from typing import List, Optional, Dict, Any
from enum import Enum
from app.models.game import Card, Suit, Rank, Player, PlayerPosition


class BidType(str, Enum):
    """亮主类型"""
    SINGLE_LEVEL = "single_level"      # 单张级牌
    PAIR_LEVEL = "pair_level"          # 级牌对子
    DOUBLE_JOKER = "double_joker"     # 双小王
    DOUBLE_BIG_JOKER = "double_big_joker"  # 双大王


class Bid:
    """亮主出价"""
    def __init__(self, player_id: str, bid_type: BidType, suit: Optional[Suit] = None):
        self.player_id = player_id
        self.bid_type = bid_type
        self.suit = suit
        self.cards: List[Card] = []
        self.priority = self._calculate_priority()
    
    def _calculate_priority(self) -> int:
        """计算反主优先级（数字越大优先级越高）"""
        priority_map = {
            BidType.SINGLE_LEVEL: 1,
            BidType.PAIR_LEVEL: 2,
            BidType.DOUBLE_JOKER: 3,
            BidType.DOUBLE_BIG_JOKER: 4
        }
        return priority_map[self.bid_type]
    
    def can_override(self, other_bid: 'Bid') -> bool:
        """判断是否可以反掉其他出价"""
        # 特殊规则：方块对子可以反双大王
        if (self.bid_type == BidType.PAIR_LEVEL and 
            self.suit == Suit.DIAMONDS and 
            other_bid.bid_type == BidType.DOUBLE_BIG_JOKER):
            return True
        
        # 正常优先级比较
        if self.priority > other_bid.priority:
            return True
        elif self.priority == other_bid.priority:
            # 同类型时，级牌对子按花色顺序比较
            if self.bid_type == BidType.PAIR_LEVEL and other_bid.bid_type == BidType.PAIR_LEVEL:
                return self._compare_suit_priority(other_bid.suit)
        return False
    
    def _compare_suit_priority(self, other_suit: Optional[Suit]) -> bool:
        """比较花色优先级（♦<♣<♥<♠）"""
        if not self.suit or not other_suit:
            return False
        
        suit_priority = {
            Suit.DIAMONDS: 1,  # ♦
            Suit.CLUBS: 2,     # ♣
            Suit.HEARTS: 3,    # ♥
            Suit.SPADES: 4     # ♠
        }
        
        return suit_priority[self.suit] > suit_priority[other_suit]


class BiddingSystem:
    """亮主和反主系统"""
    
    def __init__(self, current_level: int):
        self.current_level = current_level
        self.bids: List[Bid] = []
        self.current_bid: Optional[Bid] = None
        self.bidding_phase = True
    
    def make_bid(self, player_id: str, cards: List[Card], previous_bidding_cards: Optional[List[Card]] = None) -> Dict[str, Any]:
        """
        玩家亮主
        
        Args:
            player_id: 玩家ID
            cards: 出的牌列表
            previous_bidding_cards: 该玩家之前打出的牌（用于凑对逻辑）
        """
        if not self.bidding_phase:
            return {"success": False, "message": "亮主阶段已结束"}
        
        # 验证牌型（支持凑对逻辑）
        bid_type, suit, actual_cards = self._validate_bid_cards(cards, previous_bidding_cards)
        if not bid_type:
            return {"success": False, "message": "无效的亮主牌型"}
        
        # 需求1：不允许使用单王或对王进行初次定主，只允许在他人定主后反主
        if bid_type in [BidType.DOUBLE_JOKER, BidType.DOUBLE_BIG_JOKER]:
            if self.current_bid is None:
                return {"success": False, "message": "不能使用王进行初次定主，只能用于反主"}
        
        # 创建出价（使用实际用于反主的牌）
        bid = Bid(player_id, bid_type, suit)
        bid.cards = actual_cards  # 使用实际用于反主的牌（可能是凑对后的牌）
        
        # 检查是否可以反主
        if self.current_bid and not bid.can_override(self.current_bid):
            return {"success": False, "message": "无法反掉当前主牌"}
        
        # 更新当前出价
        self.current_bid = bid
        self.bids.append(bid)
        
        return {
            "success": True,
            "message": "亮主成功",
            "bid_type": bid_type.value,
            "suit": suit.value if suit else None,
            "priority": bid.priority,
            "actual_cards": [str(card) for card in actual_cards]  # 返回实际用于反主的牌（转换为字符串列表，用于前端显示）
        }
    
    def _validate_bid_cards(self, cards: List[Card], previous_bidding_cards: Optional[List[Card]] = None) -> tuple[Optional[BidType], Optional[Suit], List[Card]]:
        """
        验证亮主牌型，支持凑对逻辑
        
        Args:
            cards: 玩家出的牌列表
            previous_bidding_cards: 该玩家之前打出的牌（用于凑对）
        
        Returns:
            (bid_type, suit, actual_cards): 牌型、花色、实际用于反主的牌（可能是凑对后的牌）
        """
        if not cards:
            return None, None, []
        
        # 检查是否为级牌
        level_rank = self._get_level_rank()
        
        if len(cards) == 1:
            # 单张级牌
            card = cards[0]
            if not card.is_joker and card.rank == level_rank:
                # 检查是否能和之前打出的牌凑对
                if previous_bidding_cards:
                    for prev_card in previous_bidding_cards:
                        # 如果之前也打出过相同花色和级别的牌，可以凑成对子
                        if (not prev_card.is_joker and 
                            prev_card.rank == level_rank and 
                            prev_card.suit == card.suit):
                            # 凑成对子，返回级牌对子类型
                            return BidType.PAIR_LEVEL, card.suit, [prev_card, card]
                
                # 不能凑对，返回单张级牌
                return BidType.SINGLE_LEVEL, card.suit, cards
        
        elif len(cards) == 2:
            # 检查是否为级牌对子
            if self._is_level_pair(cards, level_rank):
                # 需求2：如果手上有该花色的一对级牌，默认只使用一张进行定主
                # 注意：这个逻辑只在无人定主时（初次定主）生效，反主时应该允许使用对级牌
                if self.current_bid is None:
                    # 只使用一张进行定主（返回单张级牌类型，但只使用第一张牌）
                    return BidType.SINGLE_LEVEL, cards[0].suit, [cards[0]]
                else:
                    # 反主时，允许使用对级牌
                    return BidType.PAIR_LEVEL, cards[0].suit, cards
            
            # 检查是否为双小王
            if self._is_double_joker(cards, is_big=False):
                return BidType.DOUBLE_JOKER, None, cards
            
            # 检查是否为双大王
            if self._is_double_joker(cards, is_big=True):
                return BidType.DOUBLE_BIG_JOKER, None, cards
        
        return None, None, []
    
    def _get_level_rank(self) -> Rank:
        """获取当前级别的牌面"""
        level_ranks = {
            2: Rank.TWO, 3: Rank.THREE, 4: Rank.FOUR, 5: Rank.FIVE,
            6: Rank.SIX, 7: Rank.SEVEN, 8: Rank.EIGHT, 9: Rank.NINE,
            10: Rank.TEN, 11: Rank.JACK, 12: Rank.QUEEN, 13: Rank.KING, 14: Rank.ACE
        }
        return level_ranks[self.current_level]
    
    def _is_level_pair(self, cards: List[Card], level_rank: Rank) -> bool:
        """检查是否为级牌对子"""
        if len(cards) != 2:
            return False
        
        card1, card2 = cards
        return (not card1.is_joker and not card2.is_joker and 
                card1.rank == level_rank and card2.rank == level_rank and
                card1.suit == card2.suit)
    
    def _is_double_joker(self, cards: List[Card], is_big: bool) -> bool:
        """检查是否为双王"""
        if len(cards) != 2:
            return False
        
        card1, card2 = cards
        if not card1.is_joker or not card2.is_joker:
            return False
        
        # 检查大小王
        if is_big:
            return (card1.rank == Rank.BIG_JOKER and card2.rank == Rank.BIG_JOKER)
        else:
            return (card1.rank == Rank.SMALL_JOKER and card2.rank == Rank.SMALL_JOKER)
    
    def finish_bidding(self) -> Optional[Bid]:
        """结束亮主阶段，返回最终主牌"""
        self.bidding_phase = False
        return self.current_bid
    
    def get_bidding_status(self) -> Dict[str, Any]:
        """获取亮主状态"""
        return {
            "bidding_phase": self.bidding_phase,
            "current_bid": {
                "player_id": self.current_bid.player_id if self.current_bid else None,
                "bid_type": self.current_bid.bid_type.value if self.current_bid else None,
                "suit": self.current_bid.suit.value if self.current_bid and self.current_bid.suit else None,
                "priority": self.current_bid.priority if self.current_bid else 0
            } if self.current_bid else None,
            "total_bids": len(self.bids),
            "current_level": self.current_level
        }
    
    def get_trump_suit(self) -> Optional[Suit]:
        """获取最终主牌花色"""
        if not self.current_bid:
            return None
        
        if self.current_bid.bid_type in [BidType.DOUBLE_JOKER, BidType.DOUBLE_BIG_JOKER]:
            return None  # 无主
        else:
            return self.current_bid.suit
