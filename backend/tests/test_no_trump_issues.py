"""
测试无主情况下的两个问题：
1. 领出对小王，跟出方无主牌时被要求出黑桃
2. 甩牌梅花10+方块10，跟出方黑桃10被判定更大
"""
import sys
import os
# 添加backend目录到Python路径

import pytest
from app.models.game import Card, Suit, Rank, PlayerPosition
from app.game.card_system import CardSystem
from app.game.card_playing import CardPlayingSystem
from app.game.card_comparison import CardComparison


def create_card(suit_str: str, rank_str: str) -> Card:
    """创建卡牌的辅助函数"""
    if rank_str == "JOKER-A":
        return Card(suit=None, rank=Rank.BIG_JOKER, is_joker=True)
    elif rank_str == "JOKER-B":
        return Card(suit=None, rank=Rank.SMALL_JOKER, is_joker=True)
    
    suit_map = {"♠": Suit.SPADES, "♥": Suit.HEARTS, "♦": Suit.DIAMONDS, "♣": Suit.CLUBS}
    rank_map = {
        "2": Rank.TWO, "3": Rank.THREE, "4": Rank.FOUR, "5": Rank.FIVE,
        "6": Rank.SIX, "7": Rank.SEVEN, "8": Rank.EIGHT, "9": Rank.NINE,
        "10": Rank.TEN, "J": Rank.JACK, "Q": Rank.QUEEN, "K": Rank.KING, "A": Rank.ACE
    }
    return Card(suit=suit_map[suit_str], rank=rank_map[rank_str])


class TestNoTrumpIssues:
    """测试无主情况下的问题"""
    
    def setup_method(self):
        """每个测试前的设置"""
        self.card_system = CardSystem()
        self.card_system.current_level = 10  # 设置当前级别为10
        # 无主情况：trump_suit = None
        self.trump_suit = None
        self.card_playing = CardPlayingSystem(self.card_system, self.trump_suit)
    
    def test_issue1_pair_of_small_jokers(self):
        """
        问题1：领出对小王，跟出方无主牌时的跟牌规则
        
        场景：
        - 领出方：出对小王
        - 跟出方：无级牌和王牌，只有副牌（红心3、梅花4、黑桃3、黑桃4）
        - 尝试1：出红心3+梅花4（不同花色）
        - 尝试2：出黑桃3+黑桃4（同花色）
        """
        print("\n" + "="*60)
        print("测试问题1：领出对小王，跟出方无主牌")
        print("="*60)
        
        # 领出对小王
        led_cards = [
            create_card("", "JOKER-B"),  # 小王1
            create_card("", "JOKER-B"),  # 小王2
        ]
        
        # 跟出方手牌：只有副牌，无主牌
        player_hand = [
            create_card("♥", "3"),
            create_card("♣", "4"),
            create_card("♠", "3"),
            create_card("♠", "4"),
            create_card("♦", "5"),
        ]
        
        # 领出
        print("\n1. 领出方出牌：对小王")
        lead_result = self.card_playing.play_card(
            PlayerPosition.NORTH,
            led_cards,
            led_cards  # 领出方的手牌（简化）
        )
        print(f"   领出结果: {lead_result.success}, {lead_result.message}")
        assert lead_result.success, "领出对小王应该成功"
        
        # 尝试1：跟出红心3+梅花4（不同花色）
        print("\n2. 跟出方尝试1：红心3 + 梅花4（不同花色）")
        follow_cards_1 = [
            create_card("♥", "3"),
            create_card("♣", "4"),
        ]
        follow_result_1 = self.card_playing.play_card(
            PlayerPosition.EAST,
            follow_cards_1,
            player_hand
        )
        print(f"   跟牌结果: {follow_result_1.success}, {follow_result_1.message}")
        
        # 重置trick以便测试第二次尝试
        self.card_playing._reset_trick()
        self.card_playing.play_card(PlayerPosition.NORTH, led_cards, led_cards)
        
        # 尝试2：跟出黑桃3+黑桃4（同花色）
        print("\n3. 跟出方尝试2：黑桃3 + 黑桃4（同花色）")
        follow_cards_2 = [
            create_card("♠", "3"),
            create_card("♠", "4"),
        ]
        follow_result_2 = self.card_playing.play_card(
            PlayerPosition.EAST,
            follow_cards_2,
            player_hand
        )
        print(f"   跟牌结果: {follow_result_2.success}, {follow_result_2.message}")
        
        # 分析结果
        print("\n" + "-"*60)
        print("结果分析：")
        print(f"  - 不同花色（红心3+梅花4）: {'成功' if follow_result_1.success else '失败 - ' + follow_result_1.message}")
        print(f"  - 同花色（黑桃3+黑桃4）: {'成功' if follow_result_2.success else '失败 - ' + follow_result_2.message}")
        print("\n预期：两种情况都应该成功（因为跟出方没有主牌，可以垫任意两张牌）")
        print("="*60)
    
    def test_issue2_slingshot_level_cards(self):
        """
        问题2：甩牌梅花10+方块10，跟出方黑桃10的比较
        
        场景：
        - 当前级别：10
        - 无主（trump_suit = None）
        - 领出方甩牌：梅花10 + 方块10（两张不同花色的级牌）
        - 其他玩家：无级牌和王牌
        - 跟出方：打出黑桃10（级牌）
        - 问题：黑桃10被判定比梅花10大
        """
        print("\n" + "="*60)
        print("测试问题2：甩牌级牌，比较大小")
        print("="*60)
        
        # 领出方甩牌：梅花10 + 方块10
        slingshot_cards = [
            create_card("♣", "10"),  # 梅花10（级牌）
            create_card("♦", "10"),  # 方块10（级牌）
        ]
        
        # 领出方手牌（包含甩牌）
        leader_hand = slingshot_cards.copy()
        
        # 其他玩家手牌（用于甩牌验证）
        other_player_1_hand = [create_card("♠", "3"), create_card("♥", "4")]  # 无主牌
        other_player_2_hand = [create_card("♠", "5"), create_card("♥", "6")]  # 无主牌
        other_player_3_hand = [create_card("♠", "10")]  # 有黑桃10（级牌）
        
        # 设置所有玩家手牌（用于甩牌验证）
        self.card_playing.set_player_hands({
            PlayerPosition.NORTH: leader_hand,
            PlayerPosition.EAST: other_player_1_hand,
            PlayerPosition.SOUTH: other_player_2_hand,
            PlayerPosition.WEST: other_player_3_hand,
        })
        
        # 领出甩牌
        print("\n1. 领出方甩牌：梅花10 + 方块10")
        lead_result = self.card_playing.play_card(
            PlayerPosition.NORTH,
            slingshot_cards,
            leader_hand
        )
        print(f"   甩牌结果: {lead_result.success}, {lead_result.message}")
        
        if not lead_result.success:
            print(f"   甩牌失败原因: {lead_result.message}")
            if lead_result.forced_cards:
                print(f"   强制出的牌: {[str(c) for c in lead_result.forced_cards]}")
        
        # 测试级牌比较
        print("\n2. 测试级牌大小比较（无主情况）")
        card_comparison = CardComparison(self.card_system, self.trump_suit)
        
        club_10 = create_card("♣", "10")
        diamond_10 = create_card("♦", "10")
        spade_10 = create_card("♠", "10")
        
        value_club = card_comparison._get_card_value(club_10)
        value_diamond = card_comparison._get_card_value(diamond_10)
        value_spade = card_comparison._get_card_value(spade_10)
        
        print(f"   梅花10 值: {value_club}")
        print(f"   方块10 值: {value_diamond}")
        print(f"   黑桃10 值: {value_spade}")
        
        compare_club_spade = card_comparison.compare_cards(club_10, spade_10)
        compare_diamond_spade = card_comparison.compare_cards(diamond_10, spade_10)
        
        print(f"\n   梅花10 vs 黑桃10: {compare_club_spade} ({'梅花大' if compare_club_spade > 0 else '黑桃大' if compare_club_spade < 0 else '相等'})")
        print(f"   方块10 vs 黑桃10: {compare_diamond_spade} ({'方块大' if compare_diamond_spade > 0 else '黑桃大' if compare_diamond_spade < 0 else '相等'})")
        
        print("\n" + "-"*60)
        print("结果分析：")
        print(f"  - 所有级牌的值应该相等（都是900）")
        print(f"  - 实际值: 梅花10={value_club}, 方块10={value_diamond}, 黑桃10={value_spade}")
        print(f"  - 比较结果应该都是0（相等）")
        print("="*60)
    
    def test_card_suit_classification(self):
        """
        测试辅助：检查牌的花色分类
        """
        print("\n" + "="*60)
        print("辅助测试：检查牌的花色分类")
        print("="*60)
        
        from app.game.slingshot_logic import SlingshotLogic
        slingshot_logic = SlingshotLogic(self.card_system, self.trump_suit)
        
        # 测试各种牌的花色分类
        test_cards = [
            (create_card("", "JOKER-B"), "小王"),
            (create_card("", "JOKER-A"), "大王"),
            (create_card("♣", "10"), "梅花10（级牌）"),
            (create_card("♦", "10"), "方块10（级牌）"),
            (create_card("♠", "10"), "黑桃10（级牌）"),
            (create_card("♥", "10"), "红心10（级牌）"),
            (create_card("♠", "3"), "黑桃3（副牌）"),
            (create_card("♥", "4"), "红心4（副牌）"),
        ]
        
        print("\n牌的花色分类（_get_card_suit）：")
        for card, desc in test_cards:
            suit_str = slingshot_logic._get_card_suit(card)
            print(f"  {desc:20s} -> '{suit_str}'")
        
        print("\n说明：")
        print("  - 'trump': 主牌（王牌、级牌）")
        print("  - '♠', '♥', '♣', '♦': 副牌花色")
        print("="*60)


if __name__ == "__main__":
    """直接运行此脚本进行测试"""
    print("\n开始测试无主情况下的问题...")
    print("当前级别：10")
    print("主牌花色：无主（trump_suit = None）")
    
    test = TestNoTrumpIssues()
    
    # 测试花色分类
    test.setup_method()
    test.test_card_suit_classification()
    
    # 测试问题1
    test.setup_method()
    test.test_issue1_pair_of_small_jokers()
    
    # 测试问题2
    test.setup_method()
    test.test_issue2_slingshot_level_cards()
    
    print("\n测试完成！")

