"""
八十分出牌逻辑系统
"""
from typing import List, Optional, Dict, Any, Tuple, Set
from enum import Enum
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
        self.tractor_logic = TractorLogic(card_system.current_level)
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
            all_challenge_cards = []
            
            for other_player, other_hand in self.all_players_hands.items():
                if other_player == player:
                    continue
                
                can_challenge, challenge_cards = self.slingshot_logic.check_slingshot_challenge(
                    cards, other_hand, slingshot_suit
                )
                if can_challenge:
                    all_challenge_cards.extend(challenge_cards)
            
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
        
        # 如果一圈出完，判断获胜者
        if len(self.current_trick) == 4:
            winner = self._determine_trick_winner()
            # 设置下一墩应由赢家领出
            self.expected_leader = winner
            # 结算当墩分数：仅当赢家为闲家时累计
            if winner in self.idle_positions:
                trick_points = self._calculate_trick_points(self.current_trick)
                self.idle_score += trick_points
                # 抠底机制，只发生在最后一墩
                all_hands_empty = all(len(h) == 0 for h in self.all_players_hands.values())
                if all_hands_empty and self.bottom_cards:
                    bottom_score = self._get_bottom_score()
                    # 使用领出者的牌型判断倍率
                    led_cards_for_multiplier = self.led_cards if self.led_cards else cards
                    multiplier = self._get_last_trick_multiplier(led_cards_for_multiplier)
                    bonus = bottom_score * multiplier
                    if bonus:
                        self.idle_score += bonus
                        print(f"[抠底] 闲家赢，底牌分：{bottom_score}，倍数：{multiplier}，抠底得分：+{bonus}")
            self._reset_trick()
            return PlayResult(True, "跟牌成功", winner)
        
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
            
            # 按rank分组检查是否有对子
            from collections import Counter
            rank_counts = Counter([c.rank for c in same_suit_cards])
            has_pair = any(count >= 2 for count in rank_counts.values())
            
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
                from collections import Counter
                
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
                
                # 检查是否将对子拆成了单张
                hand_rank_counts = Counter([c.rank for c in same_suit_cards])
                follow_rank_counts = Counter([c.rank for c in same_suit_in_cards])
                for rank, count in hand_rank_counts.items():
                    if count >= 2:  # 手中有这个rank的对子
                        follow_count = follow_rank_counts.get(rank, 0)
                        # 如果手中有对子，但跟的牌中这个rank只有1张，说明拆了对子，这是不允许的
                        if follow_count == 1:
                            return PlayResult(False, "有该花色对子必须出对子，不能拆成单张")
        
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
                    # 如果跟出方有拖拉机，必须匹配同样数量和长度的拖拉机
                    if follow_tractor_count > 0:
                        # 检查数量和长度是否匹配
                        if follow_tractor_count < led_tractor_count:
                            return PlayResult(False, f"有该花色拖拉机必须出{led_tractor_count}个拖拉机（只出了{follow_tractor_count}个）")
                        
                        # 检查每个拖拉机的长度是否匹配
                        # 按长度排序后比较
                        led_lengths_sorted = sorted(led_tractor_lengths, reverse=True)
                        follow_lengths_sorted = sorted(follow_tractor_lengths, reverse=True)
                        
                        for i in range(led_tractor_count):
                            if i >= len(follow_lengths_sorted) or follow_lengths_sorted[i] < led_lengths_sorted[i]:
                                return PlayResult(False, f"拖拉机长度不匹配：需要{led_lengths_sorted[i]}对，只出了{follow_lengths_sorted[i] if i < len(follow_lengths_sorted) else 0}对")
                    else:
                        # 跟出方没有拖拉机，需要将对子数量要求增加
                        # 这个会在后续对子检查中处理
                        pass
                
                # 3. 检查对子匹配（在匹配拖拉机之后）
                # 从跟出方的牌中移除已匹配的拖拉机，避免重复计算
                remaining_follow_cards = same_suit_in_cards.copy()
                # 使用card_key来匹配和移除
                for tractor in follow_tractors:
                    tractor_keys = {self.slingshot_logic._card_key(c) for c in tractor}
                    remaining_follow_cards = [
                        c for c in remaining_follow_cards 
                        if self.slingshot_logic._card_key(c) not in tractor_keys
                    ]
                
                # 计算剩余牌中的对子数
                from collections import Counter
                remaining_follow_rank_counts = Counter([c.rank for c in remaining_follow_cards])
                remaining_pairs_in_follow = sum(1 for count in remaining_follow_rank_counts.values() if count >= 2)
                
                # 计算手牌中的对子数（不包括已出的拖拉机中的对子）
                hand_rank_counts = Counter([c.rank for c in same_suit_cards])
                pairs_in_hand = sum(1 for count in hand_rank_counts.values() if count >= 2)
                
                # 计算需要出的对子数
                # 如果跟出方没有拖拉机，需要将对子数量要求增加领出方拖拉机包含的对子数
                if follow_tractor_count == 0 and led_tractor_count > 0:
                    # 跟出方没有拖拉机，需要出的对子数 = 领出方的对子数 + 领出方拖拉机包含的对子数
                    required_pairs = led_analysis["pair_count"] + led_total_tractor_pairs
                else:
                    # 跟出方有拖拉机，只需要匹配领出方的对子数
                    required_pairs = led_analysis["pair_count"]
                
                # 如果手中有足够的对子，必须出足够的对子
                if pairs_in_hand >= required_pairs:
                    if remaining_pairs_in_follow < required_pairs:
                        return PlayResult(False, f"有该花色足够对子，必须出{required_pairs}个对子（只出了{remaining_pairs_in_follow}个）")
                else:
                    # 如果对子不足，必须将所有对子出完
                    if remaining_pairs_in_follow < pairs_in_hand:
                        return PlayResult(False, f"对子不足时必须将所有对子出完（手中有{pairs_in_hand}个对子，只出了{remaining_pairs_in_follow}个）")
                
                # 4. 检查是否将对子拆成了单张
                for rank, count in hand_rank_counts.items():
                    if count >= 2:  # 手中有这个rank的对子
                        follow_count = remaining_follow_rank_counts.get(rank, 0)
                        # 如果手中有对子，但跟的牌中这个rank只有1张，说明拆了对子，这是不允许的
                        if follow_count == 1:
                            return PlayResult(False, "有该花色对子必须出对子，不能拆成单张")
        
        return PlayResult(True, "甩牌跟牌规则检查通过")
    
    def _get_card_type(self, cards: List[Card]) -> CardType:
        """获取牌型"""
        if len(cards) == 1:
            return CardType.SINGLE
        elif len(cards) == 2:
            if self._is_pair(cards):
                return CardType.PAIR
        elif len(cards) > 2:
            if self._is_tractor(cards):
                return CardType.TRACTOR
            elif self._is_slingshot(cards):
                return CardType.SLINGSHOT
        
        return CardType.SINGLE
    
    def _is_pair(self, cards: List[Card]) -> bool:
        """检查是否为对子"""
        if len(cards) != 2:
            return False
        
        card1, card2 = cards
        return (card1.rank == card2.rank and card1.suit == card2.suit)
    
    def _is_tractor(self, cards: List[Card]) -> bool:
        """检查是否为拖拉机（连对）"""
        if len(cards) < 4 or len(cards) % 2 != 0:
            return False
        
        # 简化版本：检查是否为连续的对子
        # 实际应该根据当前级牌判断相邻关系
        pairs = [cards[i:i+2] for i in range(0, len(cards), 2)]
        
        # 检查每对是否是对子
        for pair in pairs:
            if not self._is_pair(pair):
                return False
        
        # 检查是否连续（简化版本）
        # 实际应该根据级牌判断相邻关系
        return True
    
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
        
        Returns:
            获胜的玩家位置
        """
        if len(self.current_trick) != 4:
            return self.trick_leader
        
        # 获取所有出牌
        all_cards = [cards for _, cards in self.current_trick]
        players = [player for player, _ in self.current_trick]
        
        # 获取领出的花色类型
        led_suit_str = self.slingshot_logic._get_card_suit(self.led_cards[0])
        
        # 分类：主牌和副牌
        trump_players = []
        led_suit_players = []
        other_players = []
        
        for i, cards in enumerate(all_cards):
            # 检查这组牌是否全是同花色（领出的花色）
            all_led_suit = all(self.slingshot_logic._get_card_suit(c) == led_suit_str for c in cards)
            # 检查这组牌是否全是主牌
            all_trump = all(self.slingshot_logic._get_card_suit(c) == "trump" for c in cards)
            
            if all_led_suit:
                # 全是同花色（正常跟牌）
                led_suit_players.append((i, cards, players[i]))
            elif all_trump and led_suit_str != "trump":
                # 全是主牌且领出的不是主牌（将吃）
                trump_players.append((i, cards, players[i]))
            else:
                # 其他情况：
                # - 混合花色（有主牌有副牌）
                # - 全是其他副牌
                # 这些都不参与比较（垫牌或无效跟牌）
                other_players.append((i, cards, players[i]))
        
        # 1. 如果有将吃，需要检查牌型是否匹配
        if trump_players:
            # 分析领出的牌型
            led_analysis = self.slingshot_logic._analyze_card_types(self.led_cards)
            led_pair_count = led_analysis["pair_count"]
            led_tractor_count = led_analysis["tractor_count"]
            
            # 筛选出牌型匹配的将吃玩家
            valid_trump_players = []
            for i, cards, player in trump_players:
                # 分析将吃的牌型
                trump_analysis = self.slingshot_logic._analyze_card_types(cards)
                trump_pair_count = trump_analysis["pair_count"]
                trump_tractor_count = trump_analysis["tractor_count"]
                
                # 检查牌型是否匹配
                # 将吃必须有至少相同数量的对子和拖拉机
                if trump_pair_count >= led_pair_count and trump_tractor_count >= led_tractor_count:
                    valid_trump_players.append((i, cards, player))
            
            # 如果有牌型匹配的将吃，比较主牌
            if valid_trump_players:
                # 根据甩牌的牌型决定比较方式
                if led_tractor_count > 0:
                    # 1. 甩牌有拖拉机：比较拖拉机大小
                    return self._compare_trump_by_tractor(valid_trump_players)
                elif led_pair_count > 0:
                    # 2. 甩牌有对子（无拖拉机）：比较对子大小
                    return self._compare_trump_by_pair(valid_trump_players)
                else:
                    # 3. 甩牌全是单牌：比较最大单牌，相同则先出牌者获胜
                    return self._compare_trump_by_single(valid_trump_players)
            # 如果没有牌型匹配的将吃，将吃无效，继续比较同花色
        
        # 2. 如果没有将吃，比较同花色的牌
        if led_suit_players:
            winner_idx, winner_cards, winner_player = led_suit_players[0]
            
            for i, cards, player in led_suit_players[1:]:
                # 比较每组牌中最大的牌
                max_card1 = max(winner_cards, key=lambda c: self.card_comparison._get_card_value(c))
                max_card2 = max(cards, key=lambda c: self.card_comparison._get_card_value(c))
                
                if self.card_comparison.compare_cards(max_card2, max_card1) > 0:
                    winner_idx = i
                    winner_cards = cards
                    winner_player = player
            
            return winner_player
        
        # 默认返回领出者
        return self.trick_leader
    
    def compare_cards_in_trick(self, cards1: List[Card], cards2: List[Card]) -> bool:
        """
        比较两组牌在当前轮次中的大小（直接复用_determine_trick_winner的逻辑）
        
        本质上是模拟_determine_trick_winner中比较两组牌的过程
        
        Args:
            cards1: 第一组牌
            cards2: 第二组牌
            
        Returns:
            True if cards1 > cards2, False otherwise
        """
        if not cards1 or not cards2 or not self.led_cards:
            return False
        
        # 获取领出的花色类型（复用_determine_trick_winner的逻辑）
        led_suit_str = self.slingshot_logic._get_card_suit(self.led_cards[0])
        
        # 分类：主牌和副牌（复用_determine_trick_winner的逻辑）
        cards1_all_led_suit = all(self.slingshot_logic._get_card_suit(c) == led_suit_str for c in cards1)
        cards2_all_led_suit = all(self.slingshot_logic._get_card_suit(c) == led_suit_str for c in cards2)
        cards1_all_trump = all(self.slingshot_logic._get_card_suit(c) == "trump" for c in cards1)
        cards2_all_trump = all(self.slingshot_logic._get_card_suit(c) == "trump" for c in cards2)
        
        # 1. 如果有将吃，需要检查牌型是否匹配（复用_determine_trick_winner的逻辑）
        if cards1_all_trump and cards2_all_trump and led_suit_str != "trump":
            # 分析领出的牌型
            led_analysis = self.slingshot_logic._analyze_card_types(self.led_cards)
            led_pair_count = led_analysis["pair_count"]
            led_tractor_count = led_analysis["tractor_count"]
            
            # 筛选出牌型匹配的将吃玩家（复用_determine_trick_winner的逻辑）
            cards1_analysis = self.slingshot_logic._analyze_card_types(cards1)
            cards2_analysis = self.slingshot_logic._analyze_card_types(cards2)
            cards1_pair_count = cards1_analysis["pair_count"]
            cards2_pair_count = cards2_analysis["pair_count"]
            cards1_tractor_count = cards1_analysis["tractor_count"]
            cards2_tractor_count = cards2_analysis["tractor_count"]
            
            # 检查牌型是否匹配（复用_determine_trick_winner的逻辑）
            cards1_valid = cards1_pair_count >= led_pair_count and cards1_tractor_count >= led_tractor_count
            cards2_valid = cards2_pair_count >= led_pair_count and cards2_tractor_count >= led_tractor_count
            
            if not cards1_valid:
                return False
            if not cards2_valid:
                return True
            
            # 如果有牌型匹配的将吃，比较主牌（复用_determine_trick_winner的逻辑）
            if led_tractor_count > 0:
                # 1. 甩牌有拖拉机：比较拖拉机大小
                max1 = self._get_max_tractor_card(cards1)
                max2 = self._get_max_tractor_card(cards2)
                return self.card_comparison.compare_cards(max1, max2) > 0 if max1 and max2 else False
            elif led_pair_count > 0:
                # 2. 甩牌有对子（无拖拉机）：比较对子大小
                max1 = self._get_max_pair_card(cards1)
                max2 = self._get_max_pair_card(cards2)
                return self.card_comparison.compare_cards(max1, max2) > 0 if max1 and max2 else False
            else:
                # 3. 甩牌全是单牌：比较最大单牌
                max1 = max(cards1, key=lambda c: self.card_comparison._get_card_value(c))
                max2 = max(cards2, key=lambda c: self.card_comparison._get_card_value(c))
                return self.card_comparison.compare_cards(max1, max2) > 0
        
        # 2. 如果没有将吃，比较同花色的牌（复用_determine_trick_winner的逻辑）
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
            
            # 都是单牌或没有对子/拖拉机，直接比较最大牌（复用_determine_trick_winner的逻辑）
            max_card1 = max(cards1, key=lambda c: self.card_comparison._get_card_value(c))
            max_card2 = max(cards2, key=lambda c: self.card_comparison._get_card_value(c))
            return self.card_comparison.compare_cards(max_card2, max_card1) > 0
        
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
        from collections import Counter
        
        # 按rank分组，找出对子
        rank_counts = Counter([c.rank for c in cards])
        pairs = [(rank, cards_list) for rank, cards_list in 
                 [(rank, [c for c in cards if c.rank == rank]) for rank in rank_counts.keys()]
                 if len(cards_list) >= 2]
        
        if not pairs:
            # 没有对子，返回最大的单牌
            return max(cards, key=lambda c: self.card_comparison._get_card_value(c))
        
        # 找出对子中最大的牌
        max_pair_rank, max_pair_cards = max(pairs, key=lambda p: self.card_comparison._get_card_value(p[1][0]))
        return max_pair_cards[0]
    
    def _get_max_pair_card(self, cards: List[Card]) -> Card:
        """
        获取对子中最大的牌
        
        Args:
            cards: 一组牌
        
        Returns:
            对子中最大的牌
        """
        from collections import Counter
        
        # 按rank分组，找出对子
        rank_counts = Counter([c.rank for c in cards])
        pairs = [(rank, cards_list) for rank, cards_list in 
                 [(rank, [c for c in cards if c.rank == rank]) for rank in rank_counts.keys()]
                 if len(cards_list) >= 2]
        
        if not pairs:
            # 没有对子，返回最大的单牌
            return max(cards, key=lambda c: self.card_comparison._get_card_value(c))
        
        # 找出对子中最大的牌
        max_pair_rank, max_pair_cards = max(pairs, key=lambda p: self.card_comparison._get_card_value(p[1][0]))
        return max_pair_cards[0]
    
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
        challenge_cards: List[Card]
    ) -> List[Card]:
        """
        甩牌失败后，找出强制出的牌
        
        使用与挑战检测相同的逻辑：
        1. 分解甩牌为：拖拉机、对子、单牌（互不重叠）
        2. 按优先级检查：单牌 > 对子 > 拖拉机
        3. 返回被管上的那部分的最小值
        
        Args:
            slingshot_cards: 尝试甩的牌
            challenge_cards: 能管上的牌
        
        Returns:
            强制出的牌列表
        """
        # 使用slingshot_logic的分解方法
        slingshot_tractors, slingshot_pairs, slingshot_singles = self.slingshot_logic._decompose_slingshot(slingshot_cards)
        
        # 找出挑战牌中的最大单牌
        max_challenge_card = max(challenge_cards, key=lambda c: self.card_comparison._get_card_value(c))
        
        # 优先级：单牌 > 对子 > 拖拉机
        
        # 1. 检查单牌（最高优先级）
        if slingshot_singles:
            min_single = min(slingshot_singles, key=lambda c: self.card_comparison._get_card_value(c))
            # 如果单牌被管上，返回最小单牌
            if self.card_comparison.compare_cards(max_challenge_card, min_single) > 0:
                return [min_single]
        
        # 2. 检查对子
        if slingshot_pairs:
            min_pair = min(slingshot_pairs, key=lambda pair: self.card_comparison._get_card_value(pair[0]))
            min_pair_card = min_pair[0]
            # 检查挑战者是否有对子能管上
            challenger_pair_max = self._find_max_card_in_pairs_from_cards(challenge_cards)
            if challenger_pair_max and self.card_comparison.compare_cards(challenger_pair_max, min_pair_card) > 0:
                return min_pair
        
        # 3. 检查拖拉机
        if slingshot_tractors:
            min_tractor = min(slingshot_tractors, key=lambda t: self.card_comparison._get_card_value(min(t, key=lambda c: self.card_comparison._get_card_value(c))))
            # 拖拉机被管上，返回最小拖拉机
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
