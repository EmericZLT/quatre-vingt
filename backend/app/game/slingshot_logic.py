"""
甩牌逻辑实现
Slingshot Logic Implementation

甩牌规则：
1. 一次性出多张牌（可以包含单牌、对子、拖拉机的组合）
2. 必须是同一花色
3. 必须是该花色中玩家手中最大的牌
4. 其他玩家必须跟相同数量的牌

甩牌成功条件：
- 所有牌都是同一花色
- 所有牌都是该花色中玩家手中最大的牌
- 没有其他玩家能管上

甩牌失败条件：
- 有其他玩家能出更大的牌型（同花色）
- 有其他玩家用主牌管上
"""

from typing import List, Dict, Tuple, Optional
from collections import Counter
from app.models.game import Card, Suit, Rank, PlayerPosition
from app.game.card_system import CardSystem
from app.game.card_comparison import CardComparison
from app.game.tractor_logic import TractorLogic


class SlingshotResult:
    """甩牌结果"""
    def __init__(self, is_valid: bool, reason: str = "", card_types: List[str] = None):
        self.is_valid = is_valid  # 甩牌是否有效
        self.reason = reason  # 原因
        self.card_types = card_types or []  # 牌型列表（如：["tractor", "pair", "single"]）


class SlingshotLogic:
    """甩牌逻辑"""
    
    def __init__(self, card_system: CardSystem, trump_suit: Optional[Suit] = None):
        self.card_system = card_system
        self.trump_suit = trump_suit
        self.comparison = CardComparison(card_system, trump_suit)
        self.tractor_logic = TractorLogic(card_system.current_level)
    
    def validate_slingshot(self, cards: List[Card], player_hand: List[Card]) -> SlingshotResult:
        """
        验证甩牌是否有效
        
        Args:
            cards: 要甩的牌
            player_hand: 玩家手牌
        
        Returns:
            SlingshotResult: 甩牌结果
        """
        # 1. 至少要有2张牌才能甩牌
        if len(cards) < 2:
            return SlingshotResult(False, "At least 2 cards required for slingshot")
        
        # 2. 检查所有牌是否都在手牌中
        if not self._cards_in_hand(cards, player_hand):
            return SlingshotResult(False, "Cards not in player's hand")
        
        # 3. 检查是否同一花色（或都是主牌）
        if not self._is_same_suit(cards):
            return SlingshotResult(False, "All cards must be of the same suit")
        
        # 4. 分析牌型组合
        card_types = self._analyze_card_types(cards)
        
        # 注意：甩牌是否成功由其他玩家是否能管上来决定
        # 自己手中的其他牌不影响甩牌的有效性
        return SlingshotResult(True, "Valid slingshot", card_types)
    
    def _cards_in_hand(self, cards: List[Card], hand: List[Card]) -> bool:
        """检查牌是否都在手牌中"""
        hand_counter = Counter([self._card_key(c) for c in hand])
        cards_counter = Counter([self._card_key(c) for c in cards])
        
        for card_key, count in cards_counter.items():
            if hand_counter[card_key] < count:
                return False
        return True
    
    def _card_key(self, card: Card) -> str:
        """获取牌的唯一标识"""
        return f"{card.suit}_{card.rank}"
    
    def _is_same_suit(self, cards: List[Card]) -> bool:
        """检查是否同一花色（或都是主牌）"""
        if not cards:
            return True
        
        first_suit = self._get_card_suit(cards[0])
        return all(self._get_card_suit(c) == first_suit for c in cards)
    
    def _get_card_suit(self, card: Card) -> Optional[str]:
        """
        获取牌的花色类型
        
        Returns:
            "trump": 主牌
            具体花色: 副牌花色
        """
        # 大小王
        if card.rank in [Rank.SMALL_JOKER, Rank.BIG_JOKER]:
            return "trump"
        
        # 级牌
        if card.rank.value == str(self.card_system.current_level):
            return "trump"
        
        # 主牌花色
        if self.trump_suit and card.suit == self.trump_suit:
            return "trump"
        
        # 副牌
        return card.suit.value
    
    def _are_biggest_in_suit(self, cards: List[Card], remaining_hand: List[Card], suit: str) -> bool:
        """
        检查是否都是该花色中最大的牌
        
        Args:
            cards: 要甩的牌
            remaining_hand: 剩余手牌
            suit: 花色类型
        """
        # 获取剩余手牌中同花色的牌
        same_suit_cards = [c for c in remaining_hand if self._get_card_suit(c) == suit]
        
        # 如果没有剩余同花色的牌，说明甩的牌都是最大的
        if not same_suit_cards:
            return True
        
        # 找出要甩的牌中最小的牌
        smallest_slingshot = min(cards, key=lambda c: self.comparison._get_card_value(c))
        
        # 检查剩余手牌中是否有比最小甩牌还大的牌
        for card in same_suit_cards:
            if self.comparison.compare_cards(card, smallest_slingshot) > 0:
                return False
        
        return True
    
    def _analyze_card_types(self, cards: List[Card]) -> List[str]:
        """
        分析牌型组合
        
        Returns:
            牌型列表，如：["tractor", "pair", "single"]
        """
        card_types = []
        remaining_cards = cards.copy()
        
        # 按照rank分组
        rank_groups: Dict[str, List[Card]] = {}
        for card in remaining_cards:
            key = f"{card.rank}_{card.suit}"
            if key not in rank_groups:
                rank_groups[key] = []
            rank_groups[key].append(card)
        
        # 1. 先识别拖拉机
        sorted_groups = sorted(rank_groups.items(), key=lambda x: self.comparison._get_rank_value(x[1][0].rank), reverse=True)
        
        i = 0
        while i < len(sorted_groups):
            current_key, current_cards = sorted_groups[i]
            
            # 检查是否是对子
            if len(current_cards) >= 2:
                # 尝试找连续的对子形成拖拉机
                tractor_groups = [(current_key, current_cards)]
                j = i + 1
                
                while j < len(sorted_groups):
                    next_key, next_cards = sorted_groups[j]
                    if len(next_cards) >= 2:
                        # 检查是否相邻（传入Rank而不是Card）
                        if self.tractor_logic._are_adjacent(current_cards[0].rank, next_cards[0].rank):
                            tractor_groups.append((next_key, next_cards))
                            current_cards = next_cards
                            j += 1
                        else:
                            break
                    else:
                        break
                
                # 如果找到至少2组连续对子，就是拖拉机
                if len(tractor_groups) >= 2:
                    card_types.append("tractor")
                    # 移除已识别的牌
                    for key, _ in tractor_groups:
                        sorted_groups = [(k, c) for k, c in sorted_groups if k != key]
                    i = 0  # 重新开始
                    continue
            
            i += 1
        
        # 2. 再识别对子
        for key, cards_list in sorted_groups:
            if len(cards_list) >= 2:
                card_types.append("pair")
        
        # 3. 最后识别单牌
        for key, cards_list in sorted_groups:
            if len(cards_list) == 1:
                card_types.append("single")
        
        return card_types
    
    def check_slingshot_challenge(
        self,
        slingshot_cards: List[Card],
        challenger_hand: List[Card],
        slingshot_suit: str
    ) -> Tuple[bool, List[Card]]:
        """
        检查其他玩家是否能管上甩牌
        
        规则：
        - 甩牌分解为：拖拉机、对子、单牌（互不重叠）
        - 按优先级检查：单牌 > 对子 > 拖拉机
        - 每部分找最小值与挑战者比较
        - 挑战者的牌可以灵活拆分（拖拉机可以拆成对子或单牌）
        - 只要任何一部分被管上，甩牌失败
        
        Args:
            slingshot_cards: 甩的牌
            challenger_hand: 挑战者手牌
            slingshot_suit: 甩牌的花色类型
        
        Returns:
            (能否管上, 管上的牌)
        """
        # 检查是否有同花色的牌
        same_suit_cards = [c for c in challenger_hand if self._get_card_suit(c) == slingshot_suit]
        
        if not same_suit_cards:
            return False, []
        
        # 分解甩牌为：拖拉机、对子、单牌（互不重叠）
        slingshot_tractors, slingshot_pairs, slingshot_singles = self._decompose_slingshot(slingshot_cards)
        
        # 优先级：单牌 > 对子 > 拖拉机
        # 按优先级检查，一旦被管上就立即返回
        
        # 1. 检查单牌（最高优先级）
        if slingshot_singles:
            # 找出甩牌单牌中的最小牌
            min_single = min(slingshot_singles, key=lambda c: self.comparison._get_card_value(c))
            # 检查挑战者是否有更大的单牌
            max_challenger_single = max(same_suit_cards, key=lambda c: self.comparison._get_card_value(c))
            
            if self.comparison.compare_cards(max_challenger_single, min_single) > 0:
                return True, same_suit_cards
        
        # 2. 检查对子
        if slingshot_pairs:
            # 找出甩牌对子中的最小对子
            min_pair = min(slingshot_pairs, key=lambda pair: self.comparison._get_card_value(pair[0]))
            min_pair_card = min_pair[0]
            
            # 检查挑战者是否有更大的对子（可以从拖拉机中拆出）
            challenger_pair_max = self._find_max_card_in_pairs(same_suit_cards)
            
            if challenger_pair_max and self.comparison.compare_cards(challenger_pair_max, min_pair_card) > 0:
                return True, same_suit_cards
        
        # 3. 检查拖拉机
        if slingshot_tractors:
            # 找出甩牌拖拉机中的最小拖拉机（比较拖拉机中的最小对子）
            min_tractor = min(slingshot_tractors, key=lambda t: self.comparison._get_card_value(min(t, key=lambda c: self.comparison._get_card_value(c))))
            min_tractor_card = min(min_tractor, key=lambda c: self.comparison._get_card_value(c))
            
            # 检查挑战者是否有更大的拖拉机（整体比较）
            challenger_tractor_max = self._find_max_card_in_tractors(same_suit_cards)
            
            if challenger_tractor_max and self.comparison.compare_cards(challenger_tractor_max, min_tractor_card) > 0:
                return True, same_suit_cards
        
        return False, []
    
    def _decompose_slingshot(self, cards: List[Card]) -> Tuple[List[List[Card]], List[List[Card]], List[Card]]:
        """
        将甩牌分解为拖拉机、对子、单牌（互不重叠）
        
        Returns:
            (拖拉机列表, 对子列表, 单牌列表)
        """
        tractors = []
        pairs = []
        singles = []
        
        # 统计每个rank的数量
        rank_count = {}
        rank_cards = {}
        for card in cards:
            key = self._card_key(card)
            rank_count[key] = rank_count.get(key, 0) + 1
            if key not in rank_cards:
                rank_cards[key] = []
            rank_cards[key].append(card)
        
        # 标记已使用的牌
        used_keys = set()
        
        # 1. 先识别拖拉机（两对相邻的对子）
        sorted_keys = sorted(rank_count.keys(), key=lambda k: self.comparison._get_card_value(rank_cards[k][0]), reverse=True)
        
        i = 0
        while i < len(sorted_keys):
            key1 = sorted_keys[i]
            if key1 in used_keys or rank_count[key1] < 2:
                i += 1
                continue
            
            # 尝试找相邻的对子形成拖拉机
            j = i + 1
            while j < len(sorted_keys):
                key2 = sorted_keys[j]
                if key2 in used_keys or rank_count[key2] < 2:
                    j += 1
                    continue
                
                card1 = rank_cards[key1][0]
                card2 = rank_cards[key2][0]
                
                # 检查是否相邻
                if self.tractor_logic._are_adjacent(card1.rank, card2.rank):
                    # 形成拖拉机
                    tractor = rank_cards[key1][:2] + rank_cards[key2][:2]
                    tractors.append(tractor)
                    used_keys.add(key1)
                    used_keys.add(key2)
                    break
                
                j += 1
            
            i += 1
        
        # 2. 识别剩余的对子
        for key in sorted_keys:
            if key not in used_keys and rank_count[key] >= 2:
                pairs.append(rank_cards[key][:2])
                used_keys.add(key)
        
        # 3. 剩余的都是单牌
        for key in sorted_keys:
            if key not in used_keys:
                singles.extend(rank_cards[key])
        
        return tractors, pairs, singles
    
    def _find_max_card_in_tractors(self, cards: List[Card]) -> Card:
        """找出拖拉机中的最大牌"""
        # 简化：找出所有对子中的最大牌
        rank_count = {}
        for card in cards:
            key = f"{card.rank}_{card.suit}"
            rank_count[key] = rank_count.get(key, 0) + 1
        
        # 找出所有对子
        pairs = []
        for card in cards:
            key = f"{card.rank}_{card.suit}"
            if rank_count[key] >= 2 and card not in pairs:
                pairs.append(card)
        
        if not pairs:
            return max(cards, key=lambda c: self.comparison._get_card_value(c))
        
        return max(pairs, key=lambda c: self.comparison._get_card_value(c))
    
    def _find_max_card_in_pairs(self, cards: List[Card]) -> Optional[Card]:
        """找出对子中的最大牌"""
        rank_count = {}
        for card in cards:
            key = f"{card.rank}_{card.suit}"
            rank_count[key] = rank_count.get(key, 0) + 1
        
        # 找出所有对子
        pairs = []
        for card in cards:
            key = f"{card.rank}_{card.suit}"
            if rank_count[key] >= 2 and card not in pairs:
                pairs.append(card)
        
        if not pairs:
            return None
        
        return max(pairs, key=lambda c: self.comparison._get_card_value(c))
    
    def get_required_follow_cards(
        self,
        slingshot_cards: List[Card],
        follower_hand: List[Card],
        slingshot_suit: str
    ) -> List[Card]:
        """
        获取跟牌所需的牌
        
        Args:
            slingshot_cards: 甩的牌
            follower_hand: 跟牌者手牌
            slingshot_suit: 甩牌的花色类型
        
        Returns:
            跟牌所需的牌列表
        """
        required_count = len(slingshot_cards)
        
        # 1. 获取同花色的牌
        same_suit_cards = [c for c in follower_hand if self._get_card_suit(c) == slingshot_suit]
        
        # 2. 如果同花色的牌数量 >= 甩牌数量，必须出同花色
        if len(same_suit_cards) >= required_count:
            # 按大小排序，出最小的牌
            same_suit_cards.sort(key=lambda c: self.comparison._get_card_value(c))
            return same_suit_cards[:required_count]
        
        # 3. 如果同花色的牌不够，全部出同花色，然后垫其他牌
        result = same_suit_cards.copy()
        remaining_count = required_count - len(same_suit_cards)
        
        # 获取其他牌（优先垫副牌，最后垫主牌）
        other_cards = [c for c in follower_hand if c not in same_suit_cards]
        
        # 按优先级排序：副牌 > 主牌，小牌 > 大牌
        def card_priority(card: Card) -> Tuple[int, int]:
            is_trump = 1 if self._get_card_suit(card) == "trump" else 0
            rank_value = self.comparison._get_card_value(card)
            return (is_trump, rank_value)
        
        other_cards.sort(key=card_priority)
        result.extend(other_cards[:remaining_count])
        
        return result

