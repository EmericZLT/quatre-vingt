"""
手牌排序工具
用于将玩家的手牌按照游戏规则进行排序，便于前端展示
"""
from typing import List, Optional
from app.models.game import Card, Suit, Rank


class CardSorter:
    """手牌排序工具类"""
    
    def __init__(self, current_level: int, trump_suit: Optional[Suit] = None):
        """
        初始化排序器
        
        Args:
            current_level: 当前级别（用于判断级牌）
            trump_suit: 主牌花色（如果已定主）
        """
        self.current_level = current_level
        self.trump_suit = trump_suit
        self.level_rank = self._get_level_rank()
    
    def _get_level_rank(self) -> Rank:
        """获取当前级别的牌面"""
        level_ranks = {
            2: Rank.TWO, 3: Rank.THREE, 4: Rank.FOUR, 5: Rank.FIVE,
            6: Rank.SIX, 7: Rank.SEVEN, 8: Rank.EIGHT, 9: Rank.NINE,
            10: Rank.TEN, 11: Rank.JACK, 12: Rank.QUEEN, 13: Rank.KING, 14: Rank.ACE
        }
        return level_ranks[self.current_level]
    
    def is_level_card(self, card: Card) -> bool:
        """判断是否为级牌"""
        if card.is_joker:
            return False
        return card.rank == self.level_rank
    
    def is_trump_card(self, card: Card) -> bool:
        """判断是否为主牌（级牌和主牌花色的牌）"""
        if card.is_joker:
            return True  # 王牌也是主牌
        if self.is_level_card(card):
            return True  # 级牌是主牌
        if self.trump_suit and card.suit == self.trump_suit:
            return True  # 主牌花色的牌
        return False
    
    def is_plain_suit_card(self, card: Card) -> bool:
        """判断是否为副牌（非主牌）"""
        return not self.is_trump_card(card)
    
    def sort_cards(self, cards: List[Card]) -> List[Card]:
        """
        对手牌进行排序
        
        排序规则：
        1. 左侧（主牌部分）：大王 → 小王 → 级牌（主牌花色级牌 → 其它级牌，顺序与副牌顺序一致）
        2. 右侧（副牌部分）：
           - 定主后：主牌花色的非级牌移到副牌最左侧（从大到小）
           - 其他副牌：♠ → ♥ → ♣ → ♦/特殊：梅花为主时♥ → ♠ → ♦
           - 相同花色从大到小排序
        """
        if not cards:
            return []
        # 分离王牌、级牌、主牌花色非级牌、其他副牌
        jokers = []
        master_level_cards = []
        other_level_cards_by_suit = {}
        trump_suit_non_level_cards = []
        plain_suit_cards = []
        for card in cards:
            if card.is_joker:
                jokers.append(card)
            elif self.is_level_card(card):
                if self.trump_suit and card.suit == self.trump_suit:
                    master_level_cards.append(card)
                else:
                    # 分类剩余花色级牌
                    if card.suit not in other_level_cards_by_suit:
                        other_level_cards_by_suit[card.suit] = []
                    other_level_cards_by_suit[card.suit].append(card)
            elif self.trump_suit and card.suit == self.trump_suit:
                trump_suit_non_level_cards.append(card)
            else:
                plain_suit_cards.append(card)
        # 排序王牌
        jokers.sort(key=lambda c: self._get_joker_rank(c))
        # 主牌花色的级牌直接排最左
        master_level_cards.sort(key=lambda c: self._get_suit_priority(c.suit))  # 应只有一个
        # 其它级牌按副牌顺序
        other_level_cards = []
        for suit in self._get_plain_suit_order():
            if suit in other_level_cards_by_suit:
                # 可能两个副级牌
                cards_this_suit = other_level_cards_by_suit[suit]
                # 正常只有1张，无需按rank排序，若多个同花色级牌默认靠前
                other_level_cards.extend(sorted(cards_this_suit, key=lambda c: self._get_card_rank_value(c.rank), reverse=True))
        # 主牌花色非级牌：大到小
        trump_suit_non_level_cards.sort(key=lambda c: self._get_card_rank_value(c.rank), reverse=True)
        # 副牌
        sorted_plain_suit_cards = self._sort_plain_suit_cards(plain_suit_cards)
        # 组装
        result = []
        result.extend(jokers)
        result.extend(master_level_cards)
        result.extend(other_level_cards)
        if self.trump_suit:
            result.extend(trump_suit_non_level_cards)
        result.extend(sorted_plain_suit_cards)
        return result

    # --- 增量排序支持（摸牌阶段使用：插入排序） ---
    def get_sort_key(self, card: Card):
        """
        为单张牌生成全局排序键，满足 sort_cards 的最终顺序：
        Jokers -> 主花色级牌 -> 其它级牌(按副牌花色顺序) -> 主花色非级牌(大到小) -> 副牌(按花色顺序，每门从大到小)
        返回的键越小越靠左。
        """
        # 组别：0=joker, 1=master_level, 2=other_level, 3=trump_non_level(仅当有主), 4=plain
        if card.is_joker:
            group = 0
            sub1 = self._get_joker_rank(card)  # 0 大王, 1 小王
            return (group, sub1, 0, 0)

        is_level = self.is_level_card(card)
        is_trump_suit = (self.trump_suit is not None and card.suit == self.trump_suit)

        if is_level and is_trump_suit:
            # 主花色级牌
            group = 1
            # 次序稳定即可，按花色优先级反向（无实际影响，确保确定性）
            sub1 = -self._get_suit_priority(card.suit)
            return (group, sub1, 0, 0)

        if is_level and not is_trump_suit:
            # 其他级牌，按副牌花色顺序
            group = 2
            suit_order = self._get_plain_suit_order()
            # 级牌都同一牌面，rank 次序不重要，使用 suit 在副牌顺序中的索引
            sub1 = suit_order.index(card.suit) if card.suit in suit_order else 999
            # 降序 rank（级牌同值无影响）
            sub2 = -self._get_card_rank_value(card.rank)
            return (group, sub1, sub2, 0)

        if is_trump_suit and not is_level:
            # 主花色非级牌（仅在有主时出现该组别）；按点数从大到小
            group = 3 if self.trump_suit else 4
            sub1 = -self._get_card_rank_value(card.rank)
            return (group, sub1, 0, 0)

        # 副牌（非主）
        group = 4
        suit_order = self._get_plain_suit_order()
        sub1 = suit_order.index(card.suit) if card.suit in suit_order else 999
        sub2 = -self._get_card_rank_value(card.rank)
        return (group, sub1, sub2, 0)

    def insert_sorted(self, cards: List[Card], new_card: Card) -> List[Card]:
        """
        将 new_card 按当前排序规则插入到已排序的 cards 中。
        由于每名玩家最多25张，采用线性插入可读性更高，性能足够。
        前置条件：cards 已经按本排序器规则排好序。
        """
        if not cards:
            return [new_card]
        new_key = self.get_sort_key(new_card)
        result = []
        inserted = False
        for existing in cards:
            if not inserted and new_key < self.get_sort_key(existing):
                result.append(new_card)
                inserted = True
            result.append(existing)
        if not inserted:
            result.append(new_card)
        return result

    def insert_many_sorted(self, cards: List[Card], new_cards: List[Card]) -> List[Card]:
        """
        批量将多张牌按当前规则插入到已排序的 cards 中。
        采用顺序插入，保证稳定性与可读性。
        前置条件：cards 已经按本排序器规则排好序。
        """
        result = cards[:]
        for c in new_cards:
            result = self.insert_sorted(result, c)
        return result
    
    def _sort_plain_suit_cards(self, cards: List[Card]) -> List[Card]:
        """
        排序副牌
        按花色排序（♠ → ♥ → ♣ → ♦），相同花色从大到小
        特殊规则：如果梅花为主牌，黑桃排到红心后面
        """
        if not cards:
            return []
        
        # 按花色分组
        cards_by_suit = {}
        for card in cards:
            if card.suit not in cards_by_suit:
                cards_by_suit[card.suit] = []
            cards_by_suit[card.suit].append(card)
        
        # 确定花色顺序
        suit_order = self._get_plain_suit_order()
        
        # 对每个花色的牌按大小排序（从大到小）
        for suit in cards_by_suit:
            cards_by_suit[suit].sort(key=lambda c: self._get_card_rank_value(c.rank), reverse=True)
        
        # 按花色顺序组装
        result = []
        for suit in suit_order:
            if suit in cards_by_suit:
                result.extend(cards_by_suit[suit])
        
        return result
    
    def _get_plain_suit_order(self) -> List[Suit]:
        """
        获取副牌的花色顺序
        特殊规则：如果梅花为主牌，黑桃排到红心后面（避免同色混淆）
        """
        if self.trump_suit == Suit.CLUBS:
            # 梅花为主牌时：♠ → ♥ → ♣（主牌）→ ♦，但为了避免同色，调整为：♥ → ♠ → ♦
            # 注意：这里返回的是非主牌花色的顺序，主牌花色已经在前面了
            return [Suit.HEARTS, Suit.SPADES, Suit.DIAMONDS]
        else:
            # 正常顺序：♠ → ♥ → ♣ → ♦（主牌花色会被排除）
            normal_order = [Suit.SPADES, Suit.HEARTS, Suit.CLUBS, Suit.DIAMONDS]
            # 排除主牌花色
            if self.trump_suit:
                return [s for s in normal_order if s != self.trump_suit]
            return normal_order
    
    def _get_joker_rank(self, card: Card) -> int:
        """获取王牌的排序值（大王<小王，便于大王在最左）"""
        if card.rank == Rank.BIG_JOKER:
            return 0  # 大王最左
        elif card.rank == Rank.SMALL_JOKER:
            return 1  # 小王其右
        else:
            return 99  # 理论不会出现
    
    def _get_suit_priority(self, suit: Suit) -> int:
        """获取花色优先级（用于排序级牌）：♠(4) → ♥(3) → ♣(2) → ♦(1)"""
        suit_priority = {
            Suit.SPADES: 4,    # ♠
            Suit.HEARTS: 3,     # ♥
            Suit.CLUBS: 2,      # ♣
            Suit.DIAMONDS: 1,   # ♦
        }
        return suit_priority[suit]
    
    def _get_card_rank_value(self, rank: Rank) -> int:
        """获取牌面大小值（用于排序）：2=2, 3=3, ..., K=13, A=14；大小王返回0"""
        rank_values = {
            Rank.TWO: 2, Rank.THREE: 3, Rank.FOUR: 4, Rank.FIVE: 5,
            Rank.SIX: 6, Rank.SEVEN: 7, Rank.EIGHT: 8, Rank.NINE: 9,
            Rank.TEN: 10, Rank.JACK: 11, Rank.QUEEN: 12, Rank.KING: 13, Rank.ACE: 14
        }
        # 修正，若遇到JOKER直接给0
        if rank not in rank_values:
            return 0
        return rank_values[rank]

