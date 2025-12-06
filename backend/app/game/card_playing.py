"""
八十分出牌逻辑系统
"""
from typing import List, Optional, Dict, Any, Tuple, Set
from enum import Enum
from collections import Counter
from app.models.game import Card, Suit, Rank, PlayerPosition
from app.game.card_system import CardSystem
from app.game.card_comparison import CardComparison
from app.game.tractor_logic import TractorLogic
from app.game.trump_logic import TrumpLogic
from app.game.slingshot_logic import SlingshotLogic, SlingshotResult
from app.game.card_sorter import CardSorter


class CardType(str, Enum):
    """牌型类型"""
    SINGLE = "single"           # 单张
    PAIR = "pair"              # 对子
    TRACTOR = "tractor"         # 拖拉机（连对）
    SLINGSHOT = "slingshot"     # 甩牌


class PlayResult:
    """出牌结果"""
    def __init__(self, success: bool, message: str = "", winner: Optional[PlayerPosition] = None, forced_cards: Optional[List[Card]] = None):
        self.success = success
        self.message = message
        self.winner = winner
        self.forced_cards = forced_cards  # 甩牌失败时，强制出的牌


class CardPlayingSystem:
    """出牌逻辑系统"""
    
    def __init__(self, card_system: CardSystem, trump_suit: Optional[Suit] = None):
        self.card_system = card_system
        self.trump_suit = trump_suit
        self.current_trick: List[Tuple[PlayerPosition, List[Card]]] = []
        self.trick_leader: Optional[PlayerPosition] = None
        self.led_suit: Optional[Suit] = None
        self.led_card_type: Optional[CardType] = None
        self.led_cards: List[Card] = []  # 领出的牌
        self.all_players_hands: Dict[PlayerPosition, List[Card]] = {}  # 所有玩家的手牌
        # 计分：仅记录闲家在获胜墩中的分数
        self.idle_positions: Set[PlayerPosition] = set()
        self.idle_score: int = 0
        # 轮转：上一墩赢家作为下一墩应当的领出者
        self.expected_leader: Optional[PlayerPosition] = None
        self.bottom_cards: List[Card] = []  # 新增底牌字段
        
        # 初始化子系统
        self.card_comparison = CardComparison(card_system, trump_suit)
        self.tractor_logic = TractorLogic(card_system.current_level, card_system, trump_suit)
        self.trump_logic = TrumpLogic(self.card_comparison, self.tractor_logic)
        self.slingshot_logic = SlingshotLogic(card_system, trump_suit)
    
    def set_player_hands(self, hands: Dict[PlayerPosition, List[Card]]):
        """
        设置所有玩家的手牌（用于甩牌验证）
        
        Args:
            hands: {PlayerPosition: [Card, ...], ...}
        """
        self.all_players_hands = hands.copy()

    def return_cards_sorted(self, player: PlayerPosition, cards: List[Card]) -> None:
        """
        将指定牌按当前排序规则放回到 player 的手牌中（保持有序）。
        适用于：
        - 甩牌失败后，将领出尝试的牌归还到手牌
        - 其它需要归还牌到手牌并保持展示顺序的场景
        前置：self.all_players_hands[player] 被视为已按当前规则排序
        """
        if player not in self.all_players_hands:
            self.all_players_hands[player] = []
        sorter = CardSorter(
            current_level=self.card_system.current_level,
            trump_suit=self.trump_suit
        )
        self.all_players_hands[player] = sorter.insert_many_sorted(self.all_players_hands[player], cards)
    
    def play_card(self, player: PlayerPosition, cards: List[Card], player_hand: List[Card]) -> PlayResult:
        """
        玩家出牌
        
        Args:
            player: 出牌玩家
            cards: 出的牌（可以是单张、对子、拖拉机或甩牌）
            player_hand: 玩家手牌
        
        Returns:
            PlayResult: 出牌结果
        """
        # 检查玩家是否有这些牌
        for card in cards:
            if card not in player_hand:
                return PlayResult(False, f"玩家没有这张牌: {card}")
        
        # 如果是第一家（领出）
        if len(self.current_trick) == 0:
            return self._lead_cards(player, cards, player_hand)
        else:
            return self._follow_cards(player, cards, player_hand)
    
    def _lead_cards(self, player: PlayerPosition, cards: List[Card], player_hand: List[Card]) -> PlayResult:
        """
        领出牌
        
        Args:
            player: 出牌玩家
            cards: 出的牌
            player_hand: 玩家手牌
        """
        # 校验是否由期望的玩家领出（若有设置）
        if self.expected_leader is not None and player != self.expected_leader:
            return PlayResult(False, f"应由{self.expected_leader.value}领出本墩")

        # 记录领出者
        self.trick_leader = player
        self.led_cards = cards.copy()
        self.led_card_type = self._get_card_type(cards)
        
        # 如果牌型无效，直接拒绝领出
        if self.led_card_type is None:
            return PlayResult(False, "牌型无效，无法领出")
        
        # 如果是单张或对子或拖拉机，直接领出
        if self.led_card_type in [CardType.SINGLE, CardType.PAIR, CardType.TRACTOR]:
            self.led_suit = cards[0].suit
            self.current_trick.append((player, cards))
            return PlayResult(True, "领出成功")
        
        # 如果是甩牌，需要验证
        slingshot_result = self.slingshot_logic.validate_slingshot(cards, player_hand)
        if not slingshot_result.is_valid:
            return PlayResult(False, f"甩牌无效: {slingshot_result.reason}")
        
        # 检查其他玩家能否管上甩牌
        if self.all_players_hands:
            slingshot_suit = self.slingshot_logic._get_card_suit(cards[0])
            all_challenge_cards = []  # 每个元素是一个玩家的挑战牌列表
            
            for other_player, other_hand in self.all_players_hands.items():
                if other_player == player:
                    continue
                
                can_challenge, challenge_cards = self.slingshot_logic.check_slingshot_challenge(
                    cards, other_hand, slingshot_suit
                )
                if can_challenge:
                    all_challenge_cards.append(challenge_cards)  # 使用append而不是extend，保持每个玩家的牌独立
            
            if all_challenge_cards:
                # 甩牌失败，找出被管上的最小牌
                forced_cards = self._find_forced_cards_after_failed_slingshot(
                    cards, all_challenge_cards
                )
                return PlayResult(
                    False,
                    f"甩牌失败：有人能管上。必须出: {self._cards_to_string(forced_cards)}",
                    forced_cards=forced_cards
                )
        
        # 甩牌成功，记录花色类型
        self.led_suit = self.slingshot_logic._get_card_suit(cards[0])
        self.current_trick.append((player, cards))
        
        return PlayResult(True, f"甩牌成功: {', '.join(slingshot_result.card_types)}")
    
    def _follow_cards(self, player: PlayerPosition, cards: List[Card], player_hand: List[Card]) -> PlayResult:
        """
        跟牌
        
        Args:
            player: 出牌玩家
            cards: 出的牌
            player_hand: 玩家手牌
        """
        # 检查跟牌规则
        follow_result = self._check_follow_rules(player, cards, player_hand)
        if not follow_result.success:
            return follow_result
        
        # 添加到当前圈
        self.current_trick.append((player, cards))
        
        # 如果一圈出完，重置trick
        # 注意：获胜者的判断由GameState通过current_trick_max_player_id处理，不需要在这里重新计算
        # winner设为None，由GameState根据current_trick_max_player_id确定
        if len(self.current_trick) == 4:
            self._reset_trick()
            return PlayResult(True, "跟牌成功", None)
        
        return PlayResult(True, "跟牌成功")
    
    def _check_follow_rules(self, player: PlayerPosition, cards: List[Card], player_hand: List[Card]) -> PlayResult:
        """
        检查跟牌规则
        
        Args:
            player: 出牌玩家
            cards: 出的牌
            player_hand: 玩家手牌
        """
        # 1. 检查出牌数量是否匹配
        if len(cards) != len(self.led_cards):
            return PlayResult(False, f"出牌数量不匹配：领出{len(self.led_cards)}张，跟了{len(cards)}张")
        
        # 2. 如果是甩牌，使用甩牌跟牌规则
        if self.led_card_type == CardType.SLINGSHOT:
            return self._check_slingshot_follow(cards, player_hand)
        
        # 3. 检查是否有该花色的牌
        led_suit_str = self.slingshot_logic._get_card_suit(self.led_cards[0])
        same_suit_cards = [c for c in player_hand if self.slingshot_logic._get_card_suit(c) == led_suit_str]
        
        # 4. 检查出的牌是否符合花色要求
        if same_suit_cards:
            # 有该花色，检查出的牌中该花色的数量
            same_suit_in_cards = [c for c in cards if self.slingshot_logic._get_card_suit(c) == led_suit_str]
            # 如果出的该花色牌数量少于手牌中该花色的数量，说明没有出完该花色
            if len(same_suit_in_cards) < len(same_suit_cards):
                # 检查是否有该花色的牌没有出
                for card in cards:
                    if self.slingshot_logic._get_card_suit(card) != led_suit_str:
                        return PlayResult(False, "有该花色必须出该花色")
        
        # 5. 检查牌型匹配
        if self.led_card_type == CardType.PAIR:
            return self._check_pair_follow(cards, player_hand, led_suit_str)
        elif self.led_card_type == CardType.TRACTOR:
            return self._check_tractor_follow(cards, player_hand, led_suit_str)
        
        return PlayResult(True, "跟牌规则检查通过")
    
    def _check_pair_follow(self, cards: List[Card], player_hand: List[Card], led_suit_str: str) -> PlayResult:
        """
        检查对子跟牌规则
        
        Args:
            cards: 跟的牌
            player_hand: 玩家手牌
            led_suit_str: 领出的花色类型
        """
        # 检查是否出了对子
        if not self._is_pair(cards):
            # 检查手中是否有该花色的对子
            same_suit_cards = [c for c in player_hand if self.slingshot_logic._get_card_suit(c) == led_suit_str]
            
            # 检查是否有真正的对子（必须相同rank和相同suit）
            # 使用 (rank, suit) 作为key，因为不同花色的级牌不是对子
            card_keys = [(c.rank, c.suit) for c in same_suit_cards]
            key_counts = Counter(card_keys)
            has_pair = any(count >= 2 for count in key_counts.values())
            
            if has_pair:
                return PlayResult(False, "有该花色对子必须出对子")
        
        return PlayResult(True, "对子跟牌规则检查通过")
    
    def _check_tractor_follow(self, cards: List[Card], player_hand: List[Card], led_suit_str: str) -> PlayResult:
        """
        检查拖拉机跟牌规则
        
        优先级：等长度的拖拉机 > 尽量长的拖拉机 > 对子 > 单张
        
        规则：
        1. 等长度的拖拉机：手中有等长度的拖拉机，或手中有更长的拖拉机（可以出等长度的部分）
        2. 尽量长的拖拉机：如果没有等长度的，优先出最长的拖拉机
        3. 对子补足：出完拖拉机后，如果还需要对子，用对子补足
        4. 出牌数量不能多于领出者
        
        Args:
            cards: 跟的牌
            player_hand: 玩家手牌
            led_suit_str: 领出的花色类型
        """
        # 获取该花色的牌（led_suit_str可能是主牌"trump"或副牌花色）
        same_suit_cards = [c for c in player_hand if self.slingshot_logic._get_card_suit(c) == led_suit_str]
        same_suit_in_cards = [c for c in cards if self.slingshot_logic._get_card_suit(c) == led_suit_str]
        
        # 检查是否出了拖拉机
        is_tractor = self.tractor_logic.is_tractor(cards)
        is_same_suit_tractor = self.tractor_logic.is_tractor(same_suit_in_cards) if same_suit_in_cards else False
        
        # 领出者出的是拖拉机，直接计算长度（普通出牌只有一种牌型）
        led_tractor_length = len(self.led_cards) // 2  # 领出者拖拉机的长度（对子数）
        led_pair_count = led_tractor_length  # 领出者需要跟的对子数
        
        if not is_tractor or not is_same_suit_tractor:
            # 只有当该花色的牌没有出完时，才需要检查
            if same_suit_cards and len(same_suit_in_cards) < len(same_suit_cards):
                # 分析跟出者手牌中的拖拉机、对子、单牌
                hand_tractors, hand_pairs, hand_singles = self.slingshot_logic._decompose_slingshot(same_suit_cards)
                hand_tractor_lengths = [len(t) // 2 for t in hand_tractors]  # 所有拖拉机的长度列表
                hand_max_tractor_length = max(hand_tractor_lengths) if hand_tractor_lengths else 0
                
                # 分析跟出者实际出的牌
                follow_tractors, follow_pairs, follow_singles = self.slingshot_logic._decompose_slingshot(same_suit_in_cards)
                follow_tractor_lengths = [len(t) // 2 for t in follow_tractors]
                
                # 计算跟出者实际出的对子数（拖拉机中的对子 + 独立对子）
                follow_tractor_pairs = sum(follow_tractor_lengths)
                follow_pair_count = len(follow_pairs)
                follow_total_pairs = follow_tractor_pairs + follow_pair_count
                
                # 计算跟出者手牌中的对子数（拖拉机中的对子 + 独立对子）
                hand_tractor_pairs = sum(hand_tractor_lengths)
                hand_pair_count = len(hand_pairs)
                hand_total_pairs = hand_tractor_pairs + hand_pair_count
                
                # 优先级1：等长度的拖拉机（优先）
                # 等长度有两种情况：
                # 1. 手中有恰好等长度的拖拉机
                # 2. 手中有更长的拖拉机（可以出等长度的部分）
                can_play_equal_length = False
                if led_tractor_length in hand_tractor_lengths:
                    # 情况1：手中有恰好等长度的拖拉机
                    can_play_equal_length = True
                elif hand_max_tractor_length >= led_tractor_length:
                    # 情况2：手中有更长的拖拉机，可以出等长度的部分
                    can_play_equal_length = True
                
                if can_play_equal_length:
                    # 必须出等长度的拖拉机
                    if led_tractor_length not in follow_tractor_lengths:
                        # 检查是否出了等长的拖拉机
                        return PlayResult(False, f"有该花色{led_tractor_length}对或更长的拖拉机，必须出{led_tractor_length}对拖拉机")
                # 优先级2：尽量长的拖拉机（如果没有等长度或更长的拖拉机）
                elif hand_tractors:
                    # 手中有拖拉机，但没有等长度的，优先出最长的拖拉机
                    if not follow_tractors:
                        return PlayResult(False, f"有该花色{hand_max_tractor_length}对拖拉机，应优先出尽量长的拖拉机")
                    # 检查是否出了尽量长的拖拉机
                    follow_max_tractor_length = max(follow_tractor_lengths) if follow_tractor_lengths else 0
                    if follow_max_tractor_length < hand_max_tractor_length:
                        return PlayResult(False, f"有该花色{hand_max_tractor_length}对拖拉机，应优先出尽量长的拖拉机")
                    # 如果出了尽量长的拖拉机，检查是否还需要补足对子
                    remaining_pairs_needed = led_pair_count - follow_tractor_pairs
                    if remaining_pairs_needed > 0:
                        # 还需要补足对子
                        if hand_total_pairs >= led_pair_count:
                            # 手中有足够的对子，必须出足够的对子
                            if follow_total_pairs < led_pair_count:
                                return PlayResult(False, f"出了{follow_max_tractor_length}对拖拉机后，还需{remaining_pairs_needed}个对子补足（只出了{follow_pair_count}个）")
                        else:
                            # 手牌中的对子不足，只要求出完所有对子，剩余用单张补足
                            if follow_total_pairs < hand_total_pairs:
                                return PlayResult(False, f"出了{follow_max_tractor_length}对拖拉机后，对子不足时必须将所有对子出完（手中有{hand_total_pairs}个对子，只出了{follow_total_pairs}个）")
                
                # 优先级3：对子（如果拖拉机不够）
                # 计算还需要多少对子
                effective_tractor_pairs = min(follow_tractor_pairs, led_tractor_length) if follow_tractors else 0
                remaining_pairs_needed = led_pair_count - effective_tractor_pairs
                if remaining_pairs_needed > 0:
                    # 还需要对子补足
                    if hand_total_pairs >= led_pair_count:
                        # 手中有足够的对子，必须出足够的对子
                        if follow_total_pairs < led_pair_count:
                            return PlayResult(False, f"有该花色足够对子，必须出{led_pair_count}个对子（只出了{follow_total_pairs}个）")
                    else:
                        # 对子不足，必须将所有对子出完
                        if follow_total_pairs < hand_total_pairs:
                            return PlayResult(False, f"对子不足时必须将所有对子出完（手中有{hand_total_pairs}个对子，只出了{follow_total_pairs}个）")
        
        return PlayResult(True, "拖拉机跟牌规则检查通过")
    
    def _check_slingshot_follow(self, cards: List[Card], player_hand: List[Card]) -> PlayResult:
        """
        检查甩牌跟牌规则
        
        规则：
        1. 优先匹配同样类型和数量的拖拉机（长度和数量都要匹配）
        2. 之后匹配同样数量的对子
        3. 不足时才允许出单张
        4. 如果领出方有拖拉机而跟出方没有拖拉机，对子数量要求要增加拖拉机包含的对子数
        
        Args:
            cards: 跟的牌
            player_hand: 玩家手牌
        """
        # 1. 检查数量是否匹配
        if len(cards) != len(self.led_cards):
            return PlayResult(False, f"甩牌跟牌数量不对：需要{len(self.led_cards)}张")
        
        # 获取甩牌的花色类型
        led_suit_str = self.slingshot_logic._get_card_suit(self.led_cards[0])
        
        # 获取同花色的牌（出牌前的手牌）
        same_suit_cards = [c for c in player_hand if self.slingshot_logic._get_card_suit(c) == led_suit_str]
        # 获取跟的牌中该花色的牌
        same_suit_in_cards = [c for c in cards if self.slingshot_logic._get_card_suit(c) == led_suit_str]
        
        # 检查跟的牌是否符合要求
        if same_suit_cards:
            # 如果出的该花色牌数量少于手牌中该花色的数量，说明还有该花色的牌没有出
            if len(same_suit_in_cards) < len(same_suit_cards):
                # 检查是否出了其他花色的牌（不允许）
                other_suit_in_cards = [c for c in cards if self.slingshot_logic._get_card_suit(c) != led_suit_str]
                if other_suit_in_cards:
                    return PlayResult(False, "有该花色必须出该花色")
                
                # 分析领出方和跟出方的牌型
                led_same_suit_cards = [c for c in self.led_cards if self.slingshot_logic._get_card_suit(c) == led_suit_str]
                led_analysis = self.slingshot_logic._analyze_card_types(led_same_suit_cards)
                follow_analysis = self.slingshot_logic._analyze_card_types(same_suit_in_cards)
                
                # 2. 检查拖拉机匹配（优先）
                # 获取领出方拖拉机的数量和长度
                led_tractor_count = led_analysis["tractor_count"]
                led_tractor_lengths = [t["length"] for t in led_analysis["tractors"]]
                led_total_tractor_pairs = led_analysis["tractor_total_pairs"]
                
                # 获取跟出方拖拉机的数量和长度
                follow_tractor_count = follow_analysis["tractor_count"]
                follow_tractor_lengths = [t["length"] for t in follow_analysis["tractors"]]
                
                # 为了移除已匹配的拖拉机，需要分解跟出方的牌
                follow_tractors, _, _ = self.slingshot_logic._decompose_slingshot(same_suit_in_cards)
                
                # 检查拖拉机匹配
                if led_tractor_count > 0:
                    # 领出方有拖拉机，需要检查跟出方的拖拉机匹配情况
                    
                    # 分析手牌中的拖拉机（用于判断是否有足够长的拖拉机）
                    hand_tractors, hand_pairs, hand_singles = self.slingshot_logic._decompose_slingshot(same_suit_cards)
                    hand_tractor_lengths = [len(t) // 2 for t in hand_tractors]
                    hand_max_tractor_length = max(hand_tractor_lengths) if hand_tractor_lengths else 0
                    
                    if follow_tractor_count > 0:
                        # 跟出方出了拖拉机，需要检查是否满足要求
                        
                        # 按长度从大到小排序领出方的拖拉机
                        led_lengths_sorted = sorted(led_tractor_lengths, reverse=True)
                        follow_lengths_sorted = sorted(follow_tractor_lengths, reverse=True)
                        
                        # 遍历领出方的每个拖拉机，检查跟出方是否有匹配
                        for i in range(led_tractor_count):
                            led_length = led_lengths_sorted[i]
                            
                            # 检查手牌中是否有等长或更长的拖拉机
                            has_matching_tractor = any(length >= led_length for length in hand_tractor_lengths)
                            
                            if has_matching_tractor:
                                # 情况2.2.2：手牌中有匹配长度或更长的拖拉机
                                # 要求出的牌中必须包含等长的拖拉机
                                if i >= len(follow_lengths_sorted) or follow_lengths_sorted[i] < led_length:
                                    return PlayResult(False, f"有该花色{led_length}对或更长的拖拉机，必须出{led_length}对拖拉机（只出了{follow_lengths_sorted[i] if i < len(follow_lengths_sorted) else 0}对）")
                            else:
                                # 情况2.2.1：手牌中没有匹配长度或更长的拖拉机
                                # 用跟出牌中最长的拖拉机做匹配，缺少的对子数在后续检查
                                # 这里不报错，允许用最长的拖拉机 + 对子来匹配
                                break
                    else:
                        # 跟出方没有拖拉机，需要将对子数量要求增加
                        # 这个会在后续对子检查中处理
                        pass
                
                # 3. 检查对子匹配（在匹配拖拉机之后）
                # 计算跟出方的对子数（需要考虑拖拉机可以拆分为对子的情况）
                
                # 情况1.1：领出方没有拖拉机，跟出方的拖拉机应该被视为对子
                if led_tractor_count == 0 and follow_tractor_count > 0:
                    # 不移除拖拉机，直接计算所有对子（包括拖拉机中的对子）
                    follow_card_keys = [(c.rank, c.suit) for c in same_suit_in_cards]
                    follow_key_counts = Counter(follow_card_keys)
                    remaining_pairs_in_follow = sum(1 for count in follow_key_counts.values() if count >= 2)
                else:
                    # 领出方有拖拉机，或跟出方没有拖拉机，正常移除已匹配的拖拉机
                    remaining_follow_cards = same_suit_in_cards.copy()
                    # 使用card_key来匹配和移除
                    for tractor in follow_tractors:
                        tractor_keys = {self.slingshot_logic._card_key(c) for c in tractor}
                        remaining_follow_cards = [
                            c for c in remaining_follow_cards 
                            if self.slingshot_logic._card_key(c) not in tractor_keys
                        ]
                    
                    # 计算剩余牌中的对子数
                    # 使用 (rank, suit) 作为key，因为不同花色的级牌不是对子
                    remaining_follow_card_keys = [(c.rank, c.suit) for c in remaining_follow_cards]
                    remaining_follow_key_counts = Counter(remaining_follow_card_keys)
                    remaining_pairs_in_follow = sum(1 for count in remaining_follow_key_counts.values() if count >= 2)
                
                # 计算手牌中的对子数
                hand_card_keys = [(c.rank, c.suit) for c in same_suit_cards]
                hand_key_counts = Counter(hand_card_keys)
                pairs_in_hand = sum(1 for count in hand_key_counts.values() if count >= 2)
                
                # 计算需要出的对子数
                if led_tractor_count > 0 and follow_tractor_count == 0:
                    # 情况2.1：领出方有拖拉机，跟出方没有拖拉机
                    # 需要出的对子数 = 领出方的对子数 + 领出方拖拉机包含的对子数
                    required_pairs = led_analysis["pair_count"] + led_total_tractor_pairs
                elif led_tractor_count > 0 and follow_tractor_count > 0:
                    # 情况2.2：领出方有拖拉机，跟出方也有拖拉机
                    # 计算跟出方拖拉机匹配了多少领出方的拖拉机对子数
                    
                    # 按长度排序
                    led_lengths_sorted = sorted(led_tractor_lengths, reverse=True)
                    follow_lengths_sorted = sorted(follow_tractor_lengths, reverse=True)
                    
                    # 计算已匹配的对子数
                    matched_pairs = 0
                    for i in range(min(len(led_lengths_sorted), len(follow_lengths_sorted))):
                        # 跟出方的拖拉机可以匹配领出方的拖拉机（取较小值）
                        matched_pairs += min(led_lengths_sorted[i], follow_lengths_sorted[i])
                    
                    # 计算领出方还需要匹配的对子数
                    # = 领出方拖拉机总对子数 - 已匹配的对子数 + 领出方的独立对子数
                    unmatched_tractor_pairs = led_total_tractor_pairs - matched_pairs
                    required_pairs = unmatched_tractor_pairs + led_analysis["pair_count"]
                else:
                    # 情况1：领出方没有拖拉机
                    # 只需要匹配领出方的对子数
                    required_pairs = led_analysis["pair_count"]
                
                # 如果手中有足够的对子，必须出足够的对子
                if pairs_in_hand >= required_pairs:
                    if remaining_pairs_in_follow < required_pairs:
                        return PlayResult(False, f"有该花色足够对子，必须出{required_pairs}个对子（只出了{remaining_pairs_in_follow}个）")
                else:
                    # 如果对子不足，必须将所有对子出完
                    if remaining_pairs_in_follow < pairs_in_hand:
                        return PlayResult(False, f"对子不足时必须将所有对子出完（手中有{pairs_in_hand}个对子，只出了{remaining_pairs_in_follow}个）")
        
        return PlayResult(True, "甩牌跟牌规则检查通过")
    
    def _get_card_type(self, cards: List[Card]) -> CardType:
        """获取牌型"""
        if len(cards) == 1:
            return CardType.SINGLE
        elif len(cards) == 2:
            if self._is_pair(cards):
                return CardType.PAIR
            elif self._is_slingshot(cards):
                # 两张牌且不是对子，但同一花色，为甩牌
                return CardType.SLINGSHOT
        elif len(cards) > 2:
            if self.tractor_logic.is_tractor(cards):
                return CardType.TRACTOR
            elif self._is_slingshot(cards):
                return CardType.SLINGSHOT
        
        # 当多张牌但不满足任何有效牌型时，返回None表示无效牌型
        return None
    
    def _is_pair(self, cards: List[Card]) -> bool:
        """检查是否为对子"""
        if len(cards) != 2:
            return False
        
        card1, card2 = cards
        return (card1.rank == card2.rank and card1.suit == card2.suit)
    
    def _is_slingshot(self, cards: List[Card]) -> bool:
        """检查是否为甩牌"""
        # 甩牌：将手中某门花色的多张牌一起打出
        if len(cards) < 2:
            return False
        
        # 检查是否为同一花色
        first_suit = cards[0].suit
        return all(card.suit == first_suit for card in cards)
    
    def _determine_trick_winner(self) -> PlayerPosition:
        """
        判断一圈的获胜者
        
        使用compare_cards_in_trick的逻辑来比较所有玩家的牌，
        而不是重新实现一套逻辑。这样可以确保逻辑一致性。
        
        Returns:
            获胜的玩家位置
        """
        if len(self.current_trick) != 4:
            return self.trick_leader
        
        # 获取所有出牌和玩家
        all_cards = [cards for _, cards in self.current_trick]
        players = [player for player, _ in self.current_trick]
        
        # 使用compare_cards_in_trick的逻辑，逐个比较所有玩家的牌
        # 从领出者开始，依次与后续玩家比较
        winner_idx = 0
        winner_cards = all_cards[0]
        winner_player = players[0]
        
        for i in range(1, len(all_cards)):
            cards = all_cards[i]
            # 使用compare_cards_in_trick比较当前玩家的牌是否比当前获胜者更大
            if self.compare_cards_in_trick(cards, winner_cards):
                winner_idx = i
                winner_cards = cards
                winner_player = players[i]
        
        return winner_player
    
    def _check_card_type_match(self, follow_analysis: Dict[str, Any], led_analysis: Dict[str, Any]) -> bool:
        """
        检查跟牌者的牌型是否匹配领出者的牌型
        
        考虑规则：
        - 每种长度的拖拉机都需要至少等量匹配
        - 多余的更长的拖拉机可以被拆成短的拖拉机或对子以匹配
        - 多余的拖拉机可以拆成对子，以弥补可能的对子不够的情况
        
        Args:
            follow_analysis: 跟牌者的牌型分析结果（_analyze_card_types返回）
            led_analysis: 领出者的牌型分析结果（_analyze_card_types返回）
        
        Returns:
            True if 匹配, False otherwise
        """
        # 获取领出者的拖拉机信息（按长度分组）
        led_tractors_by_length = {}
        for tractor_info in led_analysis.get("tractors", []):
            length = tractor_info["length"]
            led_tractors_by_length[length] = led_tractors_by_length.get(length, 0) + 1
        
        # 获取跟牌者的拖拉机信息（按长度分组）
        follow_tractors_by_length = {}
        for tractor_info in follow_analysis.get("tractors", []):
            length = tractor_info["length"]
            follow_tractors_by_length[length] = follow_tractors_by_length.get(length, 0) + 1
        
        # 计算跟牌者可以拆分的资源
        # 1. 独立对子数量
        available_pairs = follow_analysis.get("pair_count", 0)
        # 2. 记录从拖拉机拆分出来的对子（在拆分更长的拖拉机时产生）
        pairs_from_tractors = 0
        
        # 检查每种长度的拖拉机是否匹配
        for led_length, led_count in sorted(led_tractors_by_length.items(), reverse=True):
            # 需要匹配的拖拉机数量
            required_count = led_count
            
            # 先尝试用相同长度的拖拉机匹配
            # 注意：用于匹配的拖拉机会被从follow_tractors_by_length中减去，不能再拆成对子
            matching_count = min(follow_tractors_by_length.get(led_length, 0), required_count)
            required_count -= matching_count
            follow_tractors_by_length[led_length] = follow_tractors_by_length.get(led_length, 0) - matching_count
            
            # 如果还不够，尝试用更长的拖拉机拆分
            if required_count > 0:
                for longer_length in sorted(follow_tractors_by_length.keys(), reverse=True):
                    if longer_length > led_length and follow_tractors_by_length[longer_length] > 0:
                        # 一个更长的拖拉机可以拆成一个匹配的拖拉机 + 剩余的对子
                        # 例如：长度为3的拖拉机可以拆成1个长度为2的拖拉机（用于匹配）+ 2个对子
                        # 注意：用于匹配的那部分（长度为led_length）不能再拆成对子
                        can_split = min(follow_tractors_by_length[longer_length], required_count)
                        required_count -= can_split
                        # 从follow_tractors_by_length中减去，表示这部分已被使用（用于匹配）
                        follow_tractors_by_length[longer_length] -= can_split
                        # 拆分后剩余的对子数（这部分对子可以用来匹配领出者的对子）
                        pairs_from_tractors += can_split * (longer_length - led_length)
                        if required_count == 0:
                            break
            
            # 如果还不够，说明无法匹配
            if required_count > 0:
                return False
        
        # 检查对子是否匹配
        led_pair_count = led_analysis.get("pair_count", 0)
        # 跟牌者的对子 = 独立对子 + 从拖拉机拆分出来的对子 + 剩余未使用的拖拉机可以拆成的对子
        # 注意：
        # 1. 已经用于匹配的拖拉机（无论是相同长度的，还是拆分后用于匹配的部分）不能拆成对子
        # 2. 这些已使用的拖拉机已经在匹配过程中从follow_tractors_by_length中减去了
        # 3. 所以remaining_tractor_pairs只包含未使用的拖拉机，它们可以拆成对子
        remaining_tractor_pairs = sum(
            count * length for length, count in follow_tractors_by_length.items()
        )
        total_follow_pairs = available_pairs + pairs_from_tractors + remaining_tractor_pairs
        
        if total_follow_pairs < led_pair_count:
            return False
        
        # 如果上面的检查都通过了（每种长度的拖拉机都匹配了，对子数也足够），就认为匹配
        return True
    
    def compare_cards_in_trick(self, cards1: List[Card], cards2: List[Card]) -> bool:
        """
        比较两组牌在当前轮次中的大小
        
        Args:
            cards1: 第一组牌
            cards2: 第二组牌
            
        Returns:
            True if cards1 > cards2, False otherwise
        """
        if not cards1 or not cards2 or not self.led_cards:
            return False
        
        # 获取领出的花色类型
        led_suit_str = self.slingshot_logic._get_card_suit(self.led_cards[0])
        
        # 分类：主牌和副牌
        cards1_all_led_suit = all(self.slingshot_logic._get_card_suit(c) == led_suit_str for c in cards1)
        cards2_all_led_suit = all(self.slingshot_logic._get_card_suit(c) == led_suit_str for c in cards2)
        cards1_all_trump = all(self.slingshot_logic._get_card_suit(c) == "trump" for c in cards1)
        cards2_all_trump = all(self.slingshot_logic._get_card_suit(c) == "trump" for c in cards2)
        
        # 将吃逻辑处理
        # 1. 如果本轮最大牌（cards2）全是主牌，而当前玩家出的牌（cards1）不全是主牌，那么cards1一定不会更大
        if cards2_all_trump and not cards1_all_trump:
            return False
        
        # 2. 如果当前玩家出的牌全是主牌，而本轮最大牌不是all trump，只需要判断当前玩家出的牌的牌型是否和领出牌匹配
        if cards1_all_trump and not cards2_all_trump:
            # 分析领出的牌型
            led_analysis = self.slingshot_logic._analyze_card_types(self.led_cards)
            # 分析当前玩家出的牌的牌型
            cards1_analysis = self.slingshot_logic._analyze_card_types(cards1)
            
            # 检查牌型是否匹配（使用新的匹配函数）
            cards1_valid = self._check_card_type_match(cards1_analysis, led_analysis)
            if cards1_valid:
                # 牌型匹配，cards1（主牌）大于cards2（非主牌）
                return True
            else:
                # 牌型不匹配，cards1不能大于cards2
                return False
        
        # 3. 如果当前玩家出的牌和本轮最大牌都是all trump
        if cards1_all_trump and cards2_all_trump:
            # 首先判断当前玩家出的牌是否和领出的牌匹配
            led_analysis = self.slingshot_logic._analyze_card_types(self.led_cards)
            cards1_analysis = self.slingshot_logic._analyze_card_types(cards1)
            cards2_analysis = self.slingshot_logic._analyze_card_types(cards2)
            
            # 检查cards1牌型是否匹配（使用新的匹配函数）
            cards1_valid = self._check_card_type_match(cards1_analysis, led_analysis)
            if not cards1_valid:
                return False
            
            # cards1牌型匹配，现在比较cards1和cards2的大小
            # 复用_analyze_card_types的结果获取tractor信息
            led_tractors_info = led_analysis.get("tractors", [])
            
            if led_tractors_info:
                # 领出者有tractor，取其中最长的tractor长度
                led_max_tractor_length = max(t["length"] for t in led_tractors_info)
                
                # 需要获取实际的tractor列表来比较大小，所以需要decompose
                cards1_tractors, _, _ = self.slingshot_logic._decompose_slingshot(cards1)
                cards2_tractors, _, _ = self.slingshot_logic._decompose_slingshot(cards2)
                
                # 找出长度>=领出者最长tractor长度的tractor（可以拆分成匹配的tractor）
                cards1_matching_tractors = [t for t in cards1_tractors if len(t) // 2 >= led_max_tractor_length]
                cards2_matching_tractors = [t for t in cards2_tractors if len(t) // 2 >= led_max_tractor_length]
                
                if cards1_matching_tractors and cards2_matching_tractors:
                    # 找出最大的tractor（比较tractor中最大的牌）
                    # 注意：即使tractor长度更长，也只需要比较整个tractor中最大的牌
                    cards1_max_tractor = max(cards1_matching_tractors, key=lambda t: max(self.card_comparison._get_card_value(c) for c in t))
                    cards2_max_tractor = max(cards2_matching_tractors, key=lambda t: max(self.card_comparison._get_card_value(c) for c in t))
                    
                    cards1_max_card = max(cards1_max_tractor, key=lambda c: self.card_comparison._get_card_value(c))
                    cards2_max_card = max(cards2_max_tractor, key=lambda c: self.card_comparison._get_card_value(c))
                    
                    comparison = self.card_comparison.compare_cards(cards1_max_card, cards2_max_card)
                    if comparison > 0:
                        return True
                    elif comparison < 0:
                        return False
                    else:
                        # 同样大，先出方（cards2）更大
                        return False
                elif cards1_matching_tractors:
                    # cards1有匹配的tractor（长度>=），cards2没有，cards1更大
                    return True
                else:
                    # cards1没有匹配的tractor，cards1不能更大
                    return False
            elif led_analysis.get("pair_count", 0) > 0:
                # 领出者没有tractor而有对子，比较最大对子
                # 复用analysis结果，但需要decompose来获取实际的对子列表用于比较
                cards1_tractors, cards1_pairs, _ = self.slingshot_logic._decompose_slingshot(cards1)
                cards2_tractors, cards2_pairs, _ = self.slingshot_logic._decompose_slingshot(cards2)
                
                # 找出最大的对子（只比较最大的那一对）
                if cards1_pairs and cards2_pairs:
                    cards1_max_pair = max(cards1_pairs, key=lambda p: self.card_comparison._get_card_value(p[0]))
                    cards2_max_pair = max(cards2_pairs, key=lambda p: self.card_comparison._get_card_value(p[0]))
                    
                    cards1_max_card = max(cards1_max_pair, key=lambda c: self.card_comparison._get_card_value(c))
                    cards2_max_card = max(cards2_max_pair, key=lambda c: self.card_comparison._get_card_value(c))
                    
                    comparison = self.card_comparison.compare_cards(cards1_max_card, cards2_max_card)
                    if comparison > 0:
                        return True
                    elif comparison < 0:
                        return False
                    else:
                        # 同样大，先出方（cards2）更大
                        return False
                elif cards1_pairs:
                    # cards1有对子，cards2没有，cards1更大
                    return True
                else:
                    # cards1没有对子，cards1不能更大
                    return False
            else:
                # 领出方只有单张，比较最大单牌（只比较一张）
                cards1_max_single = max(cards1, key=lambda c: self.card_comparison._get_card_value(c))
                cards2_max_single = max(cards2, key=lambda c: self.card_comparison._get_card_value(c))
                
                comparison = self.card_comparison.compare_cards(cards1_max_single, cards2_max_single)
                if comparison > 0:
                    return True
                elif comparison < 0:
                    return False
                else:
                    # 同样大，先出方（cards2）更大
                    return False
        
        # 2. 如果没有将吃，比较同花色的牌
        if cards1_all_led_suit and cards2_all_led_suit:
            # 分析领出的牌型
            led_analysis = self.slingshot_logic._analyze_card_types(self.led_cards)
            led_pair_count = led_analysis["pair_count"]
            led_tractor_count = led_analysis["tractor_count"]
            
            # 如果有对子或拖拉机，需要检查牌型匹配
            if led_pair_count > 0 or led_tractor_count > 0:
                cards1_analysis = self.slingshot_logic._analyze_card_types(cards1)
                cards2_analysis = self.slingshot_logic._analyze_card_types(cards2)
                cards1_pair_count = cards1_analysis["pair_count"]
                cards2_pair_count = cards2_analysis["pair_count"]
                cards1_tractor_count = cards1_analysis["tractor_count"]
                cards2_tractor_count = cards2_analysis["tractor_count"]
                
                # 检查牌型匹配
                cards1_valid = cards1_pair_count >= led_pair_count and cards1_tractor_count >= led_tractor_count
                cards2_valid = cards2_pair_count >= led_pair_count and cards2_tractor_count >= led_tractor_count
                
                if not cards1_valid:
                    return False
                if not cards2_valid:
                    return True
                
                # 都匹配，根据牌型比较大小
                if led_tractor_count > 0:
                    max1 = self._get_max_tractor_card(cards1)
                    max2 = self._get_max_tractor_card(cards2)
                    return self.card_comparison.compare_cards(max1, max2) > 0 if max1 and max2 else False
                elif led_pair_count > 0:
                    max1 = self._get_max_pair_card(cards1)
                    max2 = self._get_max_pair_card(cards2)
                    return self.card_comparison.compare_cards(max1, max2) > 0 if max1 and max2 else False
            
            # 都是单牌或没有对子/拖拉机，直接比较最大牌
            max_card1 = max(cards1, key=lambda c: self.card_comparison._get_card_value(c))
            max_card2 = max(cards2, key=lambda c: self.card_comparison._get_card_value(c))
            return self.card_comparison.compare_cards(max_card1, max_card2) > 0
        
        # 其他情况（垫牌等），cards1不能大于cards2
        return False
    
    def _compare_trump_by_tractor(self, trump_players: List[Tuple[int, List[Card], PlayerPosition]]) -> PlayerPosition:
        """
        比较将吃方的拖拉机大小
        
        Args:
            trump_players: [(index, cards, player), ...]
        
        Returns:
            获胜的玩家
        """
        winner_idx, winner_cards, winner_player = trump_players[0]
        
        # 找出当前获胜者的最大拖拉机牌
        winner_tractor_max = self._get_max_tractor_card(winner_cards)
        
        for i, cards, player in trump_players[1:]:
            # 找出挑战者的最大拖拉机牌
            challenger_tractor_max = self._get_max_tractor_card(cards)
            
            # 比较拖拉机中最大的牌
            if self.card_comparison.compare_cards(challenger_tractor_max, winner_tractor_max) > 0:
                winner_idx = i
                winner_cards = cards
                winner_player = player
                winner_tractor_max = challenger_tractor_max
        
        return winner_player
    
    def _compare_trump_by_pair(self, trump_players: List[Tuple[int, List[Card], PlayerPosition]]) -> PlayerPosition:
        """
        比较将吃方的对子大小
        
        Args:
            trump_players: [(index, cards, player), ...]
        
        Returns:
            获胜的玩家
        """
        winner_idx, winner_cards, winner_player = trump_players[0]
        
        # 找出当前获胜者的最大对子牌
        winner_pair_max = self._get_max_pair_card(winner_cards)
        
        for i, cards, player in trump_players[1:]:
            # 找出挑战者的最大对子牌
            challenger_pair_max = self._get_max_pair_card(cards)
            
            # 比较对子中最大的牌
            if self.card_comparison.compare_cards(challenger_pair_max, winner_pair_max) > 0:
                winner_idx = i
                winner_cards = cards
                winner_player = player
                winner_pair_max = challenger_pair_max
        
        return winner_player
    
    def _compare_trump_by_single(self, trump_players: List[Tuple[int, List[Card], PlayerPosition]]) -> PlayerPosition:
        """
        比较将吃方的最大单牌，相同则先出牌者获胜
        
        Args:
            trump_players: [(index, cards, player), ...]
        
        Returns:
            获胜的玩家
        """
        winner_idx, winner_cards, winner_player = trump_players[0]
        
        # 找出当前获胜者的最大单牌
        winner_max = max(winner_cards, key=lambda c: self.card_comparison._get_card_value(c))
        
        for i, cards, player in trump_players[1:]:
            # 找出挑战者的最大单牌
            challenger_max = max(cards, key=lambda c: self.card_comparison._get_card_value(c))
            
            # 比较最大单牌（如果相同，先出牌者获胜，所以用 > 而不是 >=）
            if self.card_comparison.compare_cards(challenger_max, winner_max) > 0:
                winner_idx = i
                winner_cards = cards
                winner_player = player
                winner_max = challenger_max
        
        return winner_player
    
    def _get_max_tractor_card(self, cards: List[Card]) -> Card:
        """
        获取拖拉机中最大的牌
        
        Args:
            cards: 一组牌
        
        Returns:
            拖拉机中最大的牌
        """
        # 按(rank, suit)分组，找出真正的对子（不同花色的级牌不是对子）
        card_keys = [(c.rank, c.suit) for c in cards]
        key_counts = Counter(card_keys)
        pairs = [(key, cards_list) for key, cards_list in 
                 [(key, [c for c in cards if (c.rank, c.suit) == key]) for key in key_counts.keys()]
                 if len(cards_list) >= 2]
        
        if not pairs:
            # 没有对子，返回最大的单牌
            return max(cards, key=lambda c: self.card_comparison._get_card_value(c))
        
        # 找出对子中最大的牌
        max_pair_key, max_pair_cards = max(pairs, key=lambda p: self.card_comparison._get_card_value(p[1][0]))
        return max_pair_cards[0]
    
    def _get_max_pair_card(self, cards: List[Card]) -> Card:
        """
        获取对子中最大的牌
        
        Args:
            cards: 一组牌
        
        Returns:
            对子中最大的牌
        """
        # 按(rank, suit)分组，找出真正的对子（不同花色的级牌不是对子）
        card_keys = [(c.rank, c.suit) for c in cards]
        key_counts = Counter(card_keys)
        pairs = [(key, cards_list) for key, cards_list in 
                 [(key, [c for c in cards if (c.rank, c.suit) == key]) for key in key_counts.keys()]
                 if len(cards_list) >= 2]
        
        if not pairs:
            # 没有对子，返回最大的单牌
            return max(cards, key=lambda c: self.card_comparison._get_card_value(c))
        
        # 找出对子中最大的牌
        max_pair_key, max_pair_cards = max(pairs, key=lambda p: self.card_comparison._get_card_value(p[1][0]))
        return max_pair_cards[0]
    
    def _is_trump_card(self, card: Card) -> bool:
        """检查是否为主牌"""
        # 大小王是主牌
        if card.is_joker:
            return True
        
        # 级牌是主牌
        if card.rank == self.card_comparison._get_level_rank():
            return True
        
        # 主牌花色的牌是主牌
        if self.trump_suit and card.suit == self.trump_suit:
            return True
        
        return False
    
    def _reset_trick(self):
        """重置当前圈"""
        self.current_trick = []
        self.trick_leader = None
        self.led_suit = None
        self.led_card_type = None
        self.led_cards = []
    
    def get_current_trick(self) -> List[Tuple[PlayerPosition, List[Card]]]:
        """获取当前圈"""
        return self.current_trick.copy()
    
    def get_trick_status(self) -> Dict[str, Any]:
        """获取当前圈状态"""
        return {
            "trick_leader": self.trick_leader.value if self.trick_leader else None,
            "led_suit": self.led_suit if isinstance(self.led_suit, str) else (self.led_suit.value if self.led_suit else None),
            "led_card_type": self.led_card_type.value if self.led_card_type else None,
            "led_cards": [str(c) for c in self.led_cards],
            "current_trick": [
                {"player": player.value, "cards": [str(c) for c in cards]}
                for player, cards in self.current_trick
            ],
            "trick_count": len(self.current_trick),
            "idle_score": self.idle_score,
            "expected_leader": self.expected_leader.value if self.expected_leader else None,
        }

    def set_idle_positions(self, positions: List[PlayerPosition]):
        """设置闲家位置列表，用于闲家记分"""
        self.idle_positions = set(positions)

    def get_idle_score(self) -> int:
        """获取闲家累计分数"""
        return self.idle_score

    def _calculate_trick_points(self, trick: List[Tuple[PlayerPosition, List[Card]]]) -> int:
        """统计一墩中的分牌总分（5=5分，10=10分，K=10分）"""
        points = 0
        for _, cards in trick:
            for c in cards:
                if not c.is_joker:
                    if c.rank == Rank.FIVE:
                        points += 5
                    elif c.rank == Rank.TEN:
                        points += 10
                    elif c.rank == Rank.KING:
                        points += 10
        return points
    
    def _find_forced_cards_after_failed_slingshot(
        self, 
        slingshot_cards: List[Card], 
        all_challenge_cards: List[List[Card]]
    ) -> List[Card]:
        """
        甩牌失败后，找出强制出的牌
        
        使用与挑战检测相同的逻辑：
        1. 分解甩牌为：拖拉机、对子、单牌（互不重叠）
        2. 按优先级检查：单牌 > 对子 > 拖拉机
        3. 对每个玩家的挑战牌逐个判断，尽早找到最小值并返回
        
        Args:
            slingshot_cards: 尝试甩的牌
            all_challenge_cards: 每个玩家的挑战牌列表（每个元素是一个玩家的牌列表）
        
        Returns:
            强制出的牌列表
        """
        # 使用slingshot_logic的分解方法
        slingshot_tractors, slingshot_pairs, slingshot_singles = self.slingshot_logic._decompose_slingshot(slingshot_cards)
        
        # 优先级：单牌 > 对子 > 拖拉机
        # 对每个优先级，逐个检查所有玩家的挑战牌，一旦找到能管上的就立即返回
        
        # 1. 检查单牌（最高优先级）
        if slingshot_singles:
            min_single = min(slingshot_singles, key=lambda c: self.card_comparison._get_card_value(c))
            # 逐个检查每个玩家的挑战牌
            for challenge_cards in all_challenge_cards:
                if challenge_cards:
                    max_challenger_single = max(challenge_cards, key=lambda c: self.card_comparison._get_card_value(c))
                    if self.card_comparison.compare_cards(max_challenger_single, min_single) > 0:
                        # 单张被管上，立即返回最小单牌
                        return [min_single]
        
        # 2. 检查对子
        if slingshot_pairs:
            min_pair = min(slingshot_pairs, key=lambda pair: self.card_comparison._get_card_value(pair[0]))
            min_pair_card = min_pair[0]
            # 逐个检查每个玩家的挑战牌
            for challenge_cards in all_challenge_cards:
                if challenge_cards:
                    challenger_pair_max = self._find_max_card_in_pairs_from_cards(challenge_cards)
                    if challenger_pair_max and self.card_comparison.compare_cards(challenger_pair_max, min_pair_card) > 0:
                        # 对子被管上，立即返回最小对子
                        return min_pair
        
        # 3. 检查拖拉机
        if slingshot_tractors:
            # 按拖拉机长度分组
            tractors_by_length = {}
            for tractor in slingshot_tractors:
                length = len(tractor) // 2
                if length not in tractors_by_length:
                    tractors_by_length[length] = []
                tractors_by_length[length].append(tractor)
            
            # 对每个长度的拖拉机，逐个检查所有玩家的挑战牌
            for length, tractors in tractors_by_length.items():
                # 找出该长度甩牌拖拉机中的最小拖拉机
                min_tractor = min(tractors, key=lambda t: self.card_comparison._get_card_value(min(t, key=lambda c: self.card_comparison._get_card_value(c))))
                min_tractor_card = min(min_tractor, key=lambda c: self.card_comparison._get_card_value(c))
                
                # 逐个检查每个玩家的挑战牌
                for challenge_cards in all_challenge_cards:
                    if not challenge_cards:
                        continue
                    
                    # 分解挑战者的牌
                    challenger_tractors, challenger_pairs, _ = self.slingshot_logic._decompose_slingshot(challenge_cards)
                    
                    # 按长度分组挑战者的拖拉机
                    challenger_tractors_by_length = {}
                    for tractor in challenger_tractors:
                        t_length = len(tractor) // 2
                        if t_length not in challenger_tractors_by_length:
                            challenger_tractors_by_length[t_length] = []
                        challenger_tractors_by_length[t_length].append(tractor)
                    
                    can_challenge = False
                    
                    # 检查相同长度的拖拉机
                    if length in challenger_tractors_by_length:
                        for challenger_tractor in challenger_tractors_by_length[length]:
                            challenger_max_pair = max(challenger_tractor, key=lambda c: self.card_comparison._get_card_value(c))
                            if self.card_comparison.compare_cards(challenger_max_pair, min_tractor_card) > 0:
                                can_challenge = True
                                break
                    
                    # 检查更长的拖拉机（可以拆分成该长度的拖拉机）
                    if not can_challenge:
                        for longer_length in challenger_tractors_by_length.keys():
                            if longer_length > length:
                                for challenger_tractor in challenger_tractors_by_length[longer_length]:
                                    extracted_tractor = challenger_tractor[:length * 2]
                                    extracted_max_pair = max(extracted_tractor, key=lambda c: self.card_comparison._get_card_value(c))
                                    if self.card_comparison.compare_cards(extracted_max_pair, min_tractor_card) > 0:
                                        can_challenge = True
                                        break
                                if can_challenge:
                                    break
                    
                    # 如果该长度的拖拉机被管上，立即返回最小拖拉机
                    if can_challenge:
                        return min_tractor
        
        # 兜底：返回第一张牌
        return [slingshot_cards[0]]
    
    def _find_max_card_in_pairs_from_cards(self, cards: List[Card]) -> Optional[Card]:
        """从给定的牌中找出最大的对子牌"""
        rank_count = {}
        rank_cards = {}
        for card in cards:
            key = self._card_key(card)
            rank_count[key] = rank_count.get(key, 0) + 1
            if key not in rank_cards:
                rank_cards[key] = []
            rank_cards[key].append(card)
        
        pairs = []
        for key, count in rank_count.items():
            if count >= 2:
                pairs.append(rank_cards[key][0])
        
        if not pairs:
            return None
        
        return max(pairs, key=lambda c: self.card_comparison._get_card_value(c))
    
    def _card_key(self, card: Card) -> str:
        """生成牌的唯一标识"""
        if card.is_joker:
            return f"JOKER-{card.rank.value}"
        return f"{card.suit.value}-{card.rank.value}"
    
    def _cards_to_string(self, cards: List[Card]) -> str:
        """将牌列表转换为字符串"""
        card_strs = []
        for card in cards:
            if card.is_joker:
                card_strs.append(f"{'小王' if card.rank == Rank.SMALL_JOKER else '大王'}")
            else:
                suit_name = {'♠': '黑桃', '♥': '红桃', '♦': '方块', '♣': '梅花'}[card.suit.value]
                rank_name = card.rank.value
                card_strs.append(f"{suit_name}{rank_name}")
        return ", ".join(card_strs)

    def set_bottom_cards(self, cards: List[Card]):
        """设置底牌列表"""
        self.bottom_cards = cards.copy() if cards else []

    def _get_bottom_score(self) -> int:
        """计算底牌分"""
        return sum(self.card_system.get_card_score(card) for card in self.bottom_cards)

    def _get_last_trick_multiplier(self, cards: List[Card]) -> int:
        """根据出牌的牌型计算底分倍率：单牌*2，对子*4，连对*8、16...，甩牌取最大"""
        tractors, pairs, singles = self.slingshot_logic._decompose_slingshot(cards)
        multipliers = [2] * len(singles)
        multipliers += [4] * len(pairs)
        # 连对每多1对×2
        for t in tractors:
            # t: 连对长度为2n，n为对数
            n = len(t) // 2
            if n >= 2:
                multipliers.append(2 ** (n + 1)) # n=2时8，n=3时16...
            else:
                multipliers.append(4) # 普通一对当对子
        if multipliers:
            return max(multipliers)
        return 2 # 默认视为单牌
