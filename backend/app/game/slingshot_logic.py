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

from typing import List, Dict, Tuple, Optional, Any
from collections import Counter, defaultdict
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
        self.tractor_logic = TractorLogic(card_system.current_level, card_system, trump_suit)
    
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
        analysis = self._analyze_card_types(cards)
        card_types = analysis["card_types"]  # 使用兼容的card_types字段
        
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
        
        # 级牌（使用 CardSystem 的方法判断）
        if card.rank == self.card_system.get_level_rank():
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
    
    def _analyze_card_types(self, cards: List[Card]) -> Dict[str, any]:
        """
        分析牌型组合，返回详细信息
        
        Returns:
            包含牌型详细信息的字典：
            {
                "tractors": [{"length": 2, "pairs": 2}, ...],  # 每个拖拉机的长度（对子数）
                "tractor_count": 2,  # 拖拉机数量
                "tractor_total_pairs": 4,  # 拖拉机总共包含的对子数
                "pair_count": 1,  # 对子数量
                "single_count": 2,  # 单牌数量
                "card_types": ["tractor", "pair", "single"]  # 兼容旧接口的牌型列表
            }
        """
        result: Dict[str, Any] = {
            "tractors": [],
            "tractor_count": 0,
            "tractor_total_pairs": 0,
            "pair_count": 0,
            "single_count": 0,
            "card_types": []
        }
        
        # 使用_decompose_slingshot来分解牌
        tractors, pairs, singles = self._decompose_slingshot(cards)
        
        # 统计拖拉机信息
        result["tractor_count"] = len(tractors)
        for tractor in tractors:
            tractor_length = len(tractor) // 2  # 拖拉机长度（对子数）
            result["tractors"].append({"length": tractor_length, "pairs": tractor_length})
            result["tractor_total_pairs"] += tractor_length
            result["card_types"].append("tractor")
        
        # 统计对子信息
        result["pair_count"] = len(pairs)
        for _ in pairs:
            result["card_types"].append("pair")
        
        # 统计单牌信息
        result["single_count"] = len(singles)
        for _ in singles:
            result["card_types"].append("single")
        
        return result
    
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
            min_pair = min(slingshot_pairs, key=lambda pair: self.comparison._get_card_value(pair[0]))
            min_pair_card = min_pair[0]
            
            # 检查挑战者是否有更大的对子
            challenger_pair_max = self._find_max_card_in_pairs(same_suit_cards)
            
            if challenger_pair_max and self.comparison.compare_cards(challenger_pair_max, min_pair_card) > 0:
                return True, same_suit_cards
        
        # 3. 检查拖拉机（按长度分组，独立检查）
        if slingshot_tractors:
            # 按拖拉机长度分组
            tractors_by_length = {}
            for tractor in slingshot_tractors:
                length = len(tractor) // 2  # 拖拉机长度（对子数）
                if length not in tractors_by_length:
                    tractors_by_length[length] = []
                tractors_by_length[length].append(tractor)
            
            # 分解挑战者的牌，获取所有可能的拖拉机
            challenger_tractors, challenger_pairs, _ = self._decompose_slingshot(same_suit_cards)
            
            # 按长度分组挑战者的拖拉机
            challenger_tractors_by_length = {}
            for tractor in challenger_tractors:
                length = len(tractor) // 2
                if length not in challenger_tractors_by_length:
                    challenger_tractors_by_length[length] = []
                challenger_tractors_by_length[length].append(tractor)
            
            # 对每个长度的拖拉机独立检查
            for length, tractors in tractors_by_length.items():
                # 找出该长度甩牌拖拉机中的最小拖拉机（比较最小对子）
                min_tractor = min(tractors, key=lambda t: self.comparison._get_card_value(min(t, key=lambda c: self.comparison._get_card_value(c))))
                min_tractor_card = min(min_tractor, key=lambda c: self.comparison._get_card_value(c))
                
                # 检查挑战者是否有更大的拖拉机可以管上
                # 挑战者可以用相同长度或更长的拖拉机来管上
                can_challenge = False
                
                # 1. 检查相同长度的拖拉机
                if length in challenger_tractors_by_length:
                    for challenger_tractor in challenger_tractors_by_length[length]:
                        # 比较拖拉机中的最大对子
                        challenger_max_pair = max(challenger_tractor, key=lambda c: self.comparison._get_card_value(c))
                        if self.comparison.compare_cards(challenger_max_pair, min_tractor_card) > 0:
                            can_challenge = True
                            break
                
                # 2. 检查更长的拖拉机（可以拆分成该长度的拖拉机）
                if not can_challenge:
                    for longer_length in challenger_tractors_by_length.keys():
                        if longer_length > length:
                            for challenger_tractor in challenger_tractors_by_length[longer_length]:
                                # 从长拖拉机中提取前length对，检查是否可以管上
                                # 拖拉机是按顺序排列的，前length对就是前length*2张牌
                                extracted_tractor = challenger_tractor[:length * 2]
                                extracted_max_pair = max(extracted_tractor, key=lambda c: self.comparison._get_card_value(c))
                                if self.comparison.compare_cards(extracted_max_pair, min_tractor_card) > 0:
                                    can_challenge = True
                                    break
                            if can_challenge:
                                break
                
                # 3. 如果该长度的拖拉机被管上，甩牌失败
                if can_challenge:
                    return True, same_suit_cards
        
        return False, []
    
    def _decompose_slingshot(self, cards: List[Card]) -> Tuple[List[List[Card]], List[List[Card]], List[Card]]:
        """
        将甩牌分解为拖拉机、对子、单牌（互不重叠）
        
        使用与_is_tractor相同的逻辑来识别拖拉机，正确处理：
        - 副牌：跳过级牌的特殊判断
        - 主牌：大小王、主副级牌的特殊情况
        
        Returns:
            (拖拉机列表, 对子列表, 单牌列表)
        """
        tractors = []
        pairs = []
        singles = []
        
        # 按花色分组（因为拖拉机必须同一花色）
        suit_groups = defaultdict(list)
        for card in cards:
            suit = self._get_card_suit(card)
            suit_groups[suit].append(card)
        
        # 标记已使用的牌（使用列表，因为Card对象不可哈希）
        used_cards = []
        
        # 对每个花色分别处理
        for suit, suit_cards in suit_groups.items():
            # 统计该花色中每个key的数量
            rank_count = {}
            rank_cards = {}
            for card in suit_cards:
                key = self._card_key(card)
                rank_count[key] = rank_count.get(key, 0) + 1
                if key not in rank_cards:
                    rank_cards[key] = []
                rank_cards[key].append(card)
            
            # 获取该花色的所有对子
            pair_keys = [key for key, count in rank_count.items() if count >= 2]
            
            # 识别该花色中的拖拉机
            used_keys = set()  # 跟踪已使用的key（字符串）
            
            # 特殊处理：大小王（主牌中的特殊情况）
            if suit == "trump":
                big_joker_cards = [c for c in suit_cards if c.is_joker and c.rank == Rank.BIG_JOKER]
                small_joker_cards = [c for c in suit_cards if c.is_joker and c.rank == Rank.SMALL_JOKER]
                
                if len(big_joker_cards) >= 2 and len(small_joker_cards) >= 2:
                    # 两张大王和两张小王可以构成连对
                    joker_tractor = big_joker_cards[:2] + small_joker_cards[:2]
                    tractors.append(joker_tractor)
                    used_cards.extend(joker_tractor)
                    # 标记大小王的key为已使用（避免后续重复计算）
                    big_joker_key = self._card_key(big_joker_cards[0])
                    small_joker_key = self._card_key(small_joker_cards[0])
                    used_keys.add(big_joker_key)
                    used_keys.add(small_joker_key)
                    # 移除已使用的大小王
                    big_joker_cards = big_joker_cards[2:]
                    small_joker_cards = small_joker_cards[2:]
                
                # 剩余的大小王单独处理
                if len(big_joker_cards) >= 2:
                    pairs.append(big_joker_cards[:2])
                    used_cards.extend(big_joker_cards[:2])
                    # 标记大王key为已使用
                    big_joker_key = self._card_key(big_joker_cards[0])
                    used_keys.add(big_joker_key)
                if len(small_joker_cards) >= 2:
                    pairs.append(small_joker_cards[:2])
                    used_cards.extend(small_joker_cards[:2])
                    # 标记小王key为已使用
                    small_joker_key = self._card_key(small_joker_cards[0])
                    used_keys.add(small_joker_key)
            
            # 按大小排序对子（用于识别连续关系）
            sorted_pair_keys = sorted(
                pair_keys,
                key=lambda k: self.comparison._get_card_value(rank_cards[k][0]),
                reverse=True
            )
            i = 0
            while i < len(sorted_pair_keys):
                key1 = sorted_pair_keys[i]
                if key1 in used_keys or rank_count[key1] < 2:
                    i += 1
                    continue
                
                card1 = rank_cards[key1][0]
                
                # 检查是否可以与后续对子构成拖拉机
                tractor_chain = [key1]
                current_card = card1
                
                j = i + 1
                while j < len(sorted_pair_keys):
                    key2 = sorted_pair_keys[j]
                    if key2 in used_keys or rank_count[key2] < 2:
                        j += 1
                        continue
                    
                    card2 = rank_cards[key2][0]
                    
                    # 检查两个对子是否可以构成拖拉机的一部分
                    if self._can_form_tractor_pair(current_card, card2):
                        tractor_chain.append(key2)
                        current_card = card2
                        j += 1
                    else:
                        break
                
                # 如果链长度>=2对，形成一个完整的拖拉机
                if len(tractor_chain) >= 2:
                    tractor = []
                    for key in tractor_chain:
                        pair_cards = rank_cards[key][:2]
                        tractor.extend(pair_cards)
                        used_cards.extend(pair_cards)
                        used_keys.add(key)
                    tractors.append(tractor)
                
                i += 1
            
            # 识别该花色中剩余的对子
            for key in sorted_pair_keys:
                if key not in used_keys and rank_count[key] >= 2:
                    pair_cards = rank_cards[key][:2]
                    pairs.append(pair_cards)
                    used_cards.extend(pair_cards)
                    used_keys.add(key)
            
            # 识别该花色中剩余的单牌
            for card in suit_cards:
                if card not in used_cards:
                    singles.append(card)
                    used_cards.append(card)
        
        return tractors, pairs, singles
    
    def _can_form_tractor_pair(self, card1: Card, card2: Card) -> bool:
        """
        检查两张牌（分别代表一个对子）是否可以构成拖拉机的一部分
        
        规则与_is_tractor相同：
        1. 普通牌：使用_are_adjacent检查（可以跳过级牌）
        2. 级牌：只有一对主级牌和一对副级牌可以构成连对
        3. 级牌和普通牌不能混合
        """
        # 检查是否都是级牌
        is_level1 = self.card_system.is_level_card(card1)
        is_level2 = self.card_system.is_level_card(card2)
        
        if is_level1 and is_level2:
            # 两个都是级牌
            # 只有一对主级牌和一对副级牌可以构成连对
            is_master1 = self.trump_suit and card1.suit == self.trump_suit
            is_master2 = self.trump_suit and card2.suit == self.trump_suit
            
            # 必须是一个主级牌和一个副级牌
            return (is_master1 and not is_master2) or (not is_master1 and is_master2)
        
        # 检查是否有级牌和普通牌混合（不允许）
        if (is_level1 and not is_level2) or (not is_level1 and is_level2):
            return False
        
        # 两个都是普通牌，使用_are_adjacent检查（可以跳过级牌）
        return self.tractor_logic._are_adjacent(card1.rank, card2.rank)
    
    def _find_max_card_in_pairs(self, cards: List[Card]) -> Optional[Card]:
        """找出对子中的最大牌"""
        rank_count = {}
        for card in cards:
            key = self._card_key(card)
            rank_count[key] = rank_count.get(key, 0) + 1
        
        # 找出所有对子
        pairs = []
        for card in cards:
            key = self._card_key(card)
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

