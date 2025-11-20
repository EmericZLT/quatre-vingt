"""
拖拉机（连对）逻辑系统
"""
from typing import List, Dict, Set, Optional
from app.models.game import Card, Rank, Suit
from app.game.card_system import CardSystem


class TractorLogic:
    """拖拉机逻辑处理"""
    
    def __init__(self, current_level: int, card_system: Optional[CardSystem] = None, trump_suit: Optional[Suit] = None):
        self.current_level = current_level
        self.level_rank = self._get_level_rank()
        self.card_system = card_system
        self.trump_suit = trump_suit
    
    def _get_level_rank(self) -> Rank:
        """获取当前级别的牌面"""
        level_ranks = {
            2: Rank.TWO, 3: Rank.THREE, 4: Rank.FOUR, 5: Rank.FIVE,
            6: Rank.SIX, 7: Rank.SEVEN, 8: Rank.EIGHT, 9: Rank.NINE,
            10: Rank.TEN, 11: Rank.JACK, 12: Rank.QUEEN, 13: Rank.KING, 14: Rank.ACE
        }
        return level_ranks[self.current_level]
    
    def is_tractor(self, cards: List[Card]) -> bool:
        """
        检查是否为拖拉机（连对）
        
        规则：
        1. 必须是连续的对子，例如9988是连对，9966不是
        2. 连续可以跳过级牌，例如级牌为10时，JJ99是连对，QQJJ99也是连对
        3. 级牌不能和普通牌构成连对，例如101099不是连对
        4. 级牌只能一对主级牌和一对副级牌构成连对
        5. 两对都是副级牌的对子不能构成连对（因为没有大小关系）
        6. 特殊：两张大王和两张小王一起出也是连对
        """
        if len(cards) < 4 or len(cards) % 2 != 0:
            return False
        
        if not cards:
            return False
        
        # 特殊规则：两张大王和两张小王一起出也是连对
        all_jokers = all(card.is_joker for card in cards)
        if all_jokers and len(cards) == 4:
            # 检查是否正好是两张大王和两张小王
            big_joker_count = sum(1 for card in cards if card.rank == Rank.BIG_JOKER)
            small_joker_count = sum(1 for card in cards if card.rank == Rank.SMALL_JOKER)
            if big_joker_count == 2 and small_joker_count == 2:
                return True
        
        # 拖拉机必须属于同一花色
        first_suit = cards[0].suit
        if not all(card.suit == first_suit for card in cards):
            return False
        
        # 将牌分成对子
        pairs = [cards[i:i+2] for i in range(0, len(cards), 2)]
        
        # 检查每对是否是对子
        for pair in pairs:
            if not self._is_pair(pair):
                return False
        
        # 提取每对的rank（用于判断是否连续）
        pair_ranks = []
        pair_is_level = []
        pair_is_master_level = []
        
        for pair in pairs:
            rank = pair[0].rank
            is_level = False
            is_master_level = False
            
            if self.card_system:
                is_level = self.card_system.is_level_card(pair[0])
                if is_level:
                    # 判断是否为主级牌（主牌花色的级牌）
                    if self.trump_suit and pair[0].suit == self.trump_suit:
                        is_master_level = True
            
            pair_ranks.append(rank)
            pair_is_level.append(is_level)
            pair_is_master_level.append(is_master_level)
        
        # 检查是否连续
        # 如果所有对子都是级牌，需要特殊处理
        all_level_pairs = all(pair_is_level)
        
        if all_level_pairs:
            # 所有对子都是级牌
            if len(pairs) == 2:
                # 只有两对级牌时，检查是否是一对主级牌和一对副级牌
                master_level_count = sum(pair_is_master_level)
                if master_level_count == 1:
                    # 一对主级牌和一对副级牌，可以构成连对
                    return True
                else:
                    # 两对都是副级牌或其他情况，不能构成连对
                    return False
            else:
                # 超过两对的级牌对子，不能构成连对（因为副级牌之间没有大小关系）
                return False
        
        # 检查是否有级牌和普通牌混合（不允许）
        has_level = any(pair_is_level)
        has_non_level = any(not is_level for is_level in pair_is_level)
        if has_level and has_non_level:
            # 级牌和普通牌混合，不能构成连对
            return False
        
        # 所有对子都是普通牌，检查是否连续（可以跳过级牌）
        # 使用_are_adjacent方法检查相邻关系
        for i in range(len(pair_ranks) - 1):
            rank1 = pair_ranks[i]
            rank2 = pair_ranks[i + 1]
            
            # 检查是否相邻（会考虑级牌的特殊规则，允许跳过级牌）
            if not self._are_adjacent(rank1, rank2):
                return False
        
        return True
    
    def _is_pair(self, cards: List[Card]) -> bool:
        """检查是否为对子"""
        if len(cards) != 2:
            return False
        return cards[0].rank == cards[1].rank and cards[0].suit == cards[1].suit
    
    def _group_by_suit(self, cards: List[Card]) -> Dict[Suit, List[Card]]:
        """按花色分组"""
        groups = {}
        for card in cards:
            if card.suit not in groups:
                groups[card.suit] = []
            groups[card.suit].append(card)
        return groups
    
    def _is_suit_tractor(self, cards: List[Card]) -> bool:
        """
        检查某花色是否为拖拉机（已废弃，使用is_tractor代替）
        保留此方法以保持向后兼容
        """
        return self.is_tractor(cards)
    
    def _group_by_rank(self, cards: List[Card]) -> Dict[Rank, List[Card]]:
        """按牌面分组"""
        groups = {}
        for card in cards:
            if card.rank not in groups:
                groups[card.rank] = []
            groups[card.rank].append(card)
        return groups
    
    def _has_consecutive_pairs(self, rank_groups: Dict[Rank, List[Card]]) -> bool:
        """检查是否有连续的对子"""
        # 获取所有有对子的牌面
        pair_ranks = [rank for rank, cards in rank_groups.items() if len(cards) >= 2]
        
        if len(pair_ranks) < 2:
            return False
        
        # 按牌面值排序
        sorted_ranks = sorted(pair_ranks, key=lambda r: self._get_rank_value(r))
        
        # 检查是否连续
        for i in range(len(sorted_ranks) - 1):
            if not self._are_adjacent(sorted_ranks[i], sorted_ranks[i + 1]):
                return False
        
        return True
    
    def _get_rank_value(self, rank: Rank) -> int:
        """获取牌面值用于排序"""
        rank_values = {
            Rank.TWO: 2, Rank.THREE: 3, Rank.FOUR: 4, Rank.FIVE: 5,
            Rank.SIX: 6, Rank.SEVEN: 7, Rank.EIGHT: 8, Rank.NINE: 9,
            Rank.TEN: 10, Rank.JACK: 11, Rank.QUEEN: 12, Rank.KING: 13, Rank.ACE: 14
        }
        return rank_values.get(rank, 0)
    
    def _are_adjacent(self, rank1: Rank, rank2: Rank) -> bool:
        """检查两个牌面是否相邻（根据当前级牌）"""
        # 获取所有牌面的顺序
        all_ranks = [
            Rank.TWO, Rank.THREE, Rank.FOUR, Rank.FIVE, Rank.SIX, Rank.SEVEN,
            Rank.EIGHT, Rank.NINE, Rank.TEN, Rank.JACK, Rank.QUEEN, Rank.KING, Rank.ACE
        ]
        
        # 找到级牌在顺序中的位置
        level_index = all_ranks.index(self.level_rank)
        
        # 构建相邻关系：级牌会"插入"到相邻位置之间
        # 例如：级牌是10时，9和J相邻（因为10在中间）
        adjacent_pairs = set()
        
        # 标准相邻关系
        for i in range(len(all_ranks) - 1):
            adjacent_pairs.add((all_ranks[i], all_ranks[i + 1]))
        
        # 级牌特殊处理：级牌会"打断"原有的相邻关系
        # 级牌前面的牌和级牌后面的牌相邻
        if level_index > 0 and level_index < len(all_ranks) - 1:
            # 级牌前面的牌和级牌后面的牌相邻
            adjacent_pairs.add((all_ranks[level_index - 1], all_ranks[level_index + 1]))
            # 移除被级牌打断的相邻关系
            adjacent_pairs.discard((all_ranks[level_index - 1], self.level_rank))
            adjacent_pairs.discard((self.level_rank, all_ranks[level_index + 1]))
        
        # 检查是否相邻
        return (rank1, rank2) in adjacent_pairs or (rank2, rank1) in adjacent_pairs
    
    def get_tractor_info(self, cards: List[Card]) -> Dict[str, any]:
        """获取拖拉机信息"""
        if not self.is_tractor(cards):
            return {"is_tractor": False}
        
        # 按花色分组
        suit_groups = self._group_by_suit(cards)
        
        # 找到构成拖拉机的花色
        tractor_suits = []
        for suit, suit_cards in suit_groups.items():
            if self._is_suit_tractor(suit_cards):
                tractor_suits.append(suit)
        
        return {
            "is_tractor": True,
            "tractor_suits": [suit.value for suit in tractor_suits],
            "tractor_length": len(cards) // 2  # 拖拉机长度（对子数）
        }
    
    def validate_tractor_play(self, cards: List[Card], player_cards: List[Card]) -> bool:
        """验证拖拉机出牌是否合法"""
        if not self.is_tractor(cards):
            return False
        
        # 检查玩家是否有这些牌
        for card in cards:
            if card not in player_cards:
                return False
        
        # 检查拖拉机是否完整（不能拆开）
        return True
