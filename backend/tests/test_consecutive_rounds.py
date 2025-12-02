"""
测试连续两轮游戏：第一轮有主（黑桃），第二轮无主
验证trump_suit是否正确重置，以及出牌逻辑是否正确
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

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


def test_consecutive_rounds():
    """
    测试连续两轮游戏的场景
    
    第一轮：黑桃为主，级别10
    第二轮：无主（trump_suit = None），级别10
    
    验证：
    1. 第二轮中，级牌（10）是否被正确识别为主牌
    2. 第二轮中，黑桃是否不再是主牌
    3. 第二轮中，不同花色的级牌是否大小相等
    """
    print("\n" + "="*70)
    print("测试连续两轮游戏：第一轮黑桃为主，第二轮无主")
    print("="*70)
    
    card_system = CardSystem()
    card_system.current_level = 10
    
    # ========== 第一轮：黑桃为主 ==========
    print("\n" + "-"*70)
    print("第一轮游戏：黑桃为主，级别10")
    print("-"*70)
    
    trump_suit_round1 = Suit.SPADES
    card_playing_round1 = CardPlayingSystem(card_system, trump_suit_round1)
    
    print(f"\n第一轮设置：")
    print(f"  trump_suit: {trump_suit_round1}")
    print(f"  current_level: {card_system.current_level}")
    
    # 测试第一轮的牌分类
    from app.game.slingshot_logic import SlingshotLogic
    slingshot_round1 = SlingshotLogic(card_system, trump_suit_round1)
    
    spade_10_round1 = create_card("♠", "10")
    heart_10_round1 = create_card("♥", "10")
    spade_3_round1 = create_card("♠", "3")
    
    print(f"\n第一轮牌的分类：")
    print(f"  黑桃10: {slingshot_round1._get_card_suit(spade_10_round1)} (应该是 'trump'，因为既是级牌又是主牌花色)")
    print(f"  红心10: {slingshot_round1._get_card_suit(heart_10_round1)} (应该是 'trump'，因为是级牌)")
    print(f"  黑桃3:  {slingshot_round1._get_card_suit(spade_3_round1)} (应该是 'trump'，因为是主牌花色)")
    
    # ========== 第二轮：无主 ==========
    print("\n" + "-"*70)
    print("第二轮游戏：无主，级别10")
    print("-"*70)
    
    trump_suit_round2 = None
    card_playing_round2 = CardPlayingSystem(card_system, trump_suit_round2)
    
    print(f"\n第二轮设置：")
    print(f"  trump_suit: {trump_suit_round2}")
    print(f"  current_level: {card_system.current_level}")
    
    # 测试第二轮的牌分类
    slingshot_round2 = SlingshotLogic(card_system, trump_suit_round2)
    
    spade_10_round2 = create_card("♠", "10")
    heart_10_round2 = create_card("♥", "10")
    club_10_round2 = create_card("♣", "10")
    diamond_10_round2 = create_card("♦", "10")
    spade_3_round2 = create_card("♠", "3")
    heart_3_round2 = create_card("♥", "3")
    
    print(f"\n第二轮牌的分类：")
    print(f"  黑桃10: {slingshot_round2._get_card_suit(spade_10_round2)} (应该是 'trump'，因为是级牌)")
    print(f"  红心10: {slingshot_round2._get_card_suit(heart_10_round2)} (应该是 'trump'，因为是级牌)")
    print(f"  梅花10: {slingshot_round2._get_card_suit(club_10_round2)} (应该是 'trump'，因为是级牌)")
    print(f"  方块10: {slingshot_round2._get_card_suit(diamond_10_round2)} (应该是 'trump'，因为是级牌)")
    print(f"  黑桃3:  {slingshot_round2._get_card_suit(spade_3_round2)} (应该是 '♠'，因为是副牌)")
    print(f"  红心3:  {slingshot_round2._get_card_suit(heart_3_round2)} (应该是 '♥'，因为是副牌)")
    
    # 测试第二轮的牌值比较
    card_comparison_round2 = CardComparison(card_system, trump_suit_round2)
    
    value_spade_10 = card_comparison_round2._get_card_value(spade_10_round2)
    value_heart_10 = card_comparison_round2._get_card_value(heart_10_round2)
    value_club_10 = card_comparison_round2._get_card_value(club_10_round2)
    value_diamond_10 = card_comparison_round2._get_card_value(diamond_10_round2)
    
    print(f"\n第二轮级牌的值：")
    print(f"  黑桃10: {value_spade_10}")
    print(f"  红心10: {value_heart_10}")
    print(f"  梅花10: {value_club_10}")
    print(f"  方块10: {value_diamond_10}")
    print(f"  (所有级牌的值应该都是 900)")
    
    compare_spade_heart = card_comparison_round2.compare_cards(spade_10_round2, heart_10_round2)
    compare_club_spade = card_comparison_round2.compare_cards(club_10_round2, spade_10_round2)
    compare_diamond_heart = card_comparison_round2.compare_cards(diamond_10_round2, heart_10_round2)
    
    print(f"\n第二轮级牌的比较：")
    print(f"  黑桃10 vs 红心10: {compare_spade_heart} ({'相等' if compare_spade_heart == 0 else '不相等'})")
    print(f"  梅花10 vs 黑桃10: {compare_club_spade} ({'相等' if compare_club_spade == 0 else '不相等'})")
    print(f"  方块10 vs 红心10: {compare_diamond_heart} ({'相等' if compare_diamond_heart == 0 else '不相等'})")
    print(f"  (所有比较结果应该都是 0，表示相等)")
    
    # ========== 测试问题1：领出对小王，跟出方无主牌 ==========
    print("\n" + "-"*70)
    print("测试问题1：第二轮中，领出对小王，跟出方无主牌")
    print("-"*70)
    
    led_cards = [
        create_card("", "JOKER-B"),
        create_card("", "JOKER-B"),
    ]
    
    player_hand = [
        create_card("♥", "3"),
        create_card("♣", "4"),
        create_card("♠", "3"),
        create_card("♠", "4"),
    ]
    
    # 领出
    print("\n领出方出牌：对小王")
    lead_result = card_playing_round2.play_card(
        PlayerPosition.NORTH,
        led_cards,
        led_cards
    )
    print(f"  结果: {lead_result.success}, {lead_result.message}")
    
    # 跟出：红心3 + 梅花4
    print("\n跟出方尝试：红心3 + 梅花4（不同花色）")
    follow_cards = [
        create_card("♥", "3"),
        create_card("♣", "4"),
    ]
    follow_result = card_playing_round2.play_card(
        PlayerPosition.EAST,
        follow_cards,
        player_hand
    )
    print(f"  结果: {follow_result.success}, {follow_result.message}")
    
    if follow_result.success:
        print("  ✓ 正确：跟出方没有主牌，可以垫任意两张牌")
    else:
        print(f"  ❌ 错误：跟出方应该可以垫任意两张牌，但被拒绝了")
        print(f"  错误消息: {follow_result.message}")
    
    # ========== 验证结果 ==========
    print("\n" + "="*70)
    print("验证结果：")
    print("="*70)
    
    all_correct = True
    
    # 验证1：第二轮中，黑桃不再是主牌花色
    if slingshot_round2._get_card_suit(spade_3_round2) == "♠":
        print("✓ 第二轮中，黑桃3被正确识别为副牌（不是主牌）")
    else:
        print("❌ 第二轮中，黑桃3被错误识别为主牌")
        all_correct = False
    
    # 验证2：第二轮中，所有级牌都是主牌
    if (slingshot_round2._get_card_suit(spade_10_round2) == "trump" and
        slingshot_round2._get_card_suit(heart_10_round2) == "trump" and
        slingshot_round2._get_card_suit(club_10_round2) == "trump" and
        slingshot_round2._get_card_suit(diamond_10_round2) == "trump"):
        print("✓ 第二轮中，所有级牌都被正确识别为主牌")
    else:
        print("❌ 第二轮中，级牌识别错误")
        all_correct = False
    
    # 验证3：第二轮中，所有级牌值相等
    if (value_spade_10 == value_heart_10 == value_club_10 == value_diamond_10 == 900):
        print("✓ 第二轮中，所有级牌的值都是900（相等）")
    else:
        print("❌ 第二轮中，级牌的值不相等")
        all_correct = False
    
    # 验证4：第二轮中，级牌比较结果为0
    if compare_spade_heart == 0 and compare_club_spade == 0 and compare_diamond_heart == 0:
        print("✓ 第二轮中，不同花色的级牌比较结果都是0（相等）")
    else:
        print("❌ 第二轮中，级牌比较结果不是0")
        all_correct = False
    
    # 验证5：跟出方可以垫任意两张牌
    if follow_result.success:
        print("✓ 第二轮中，跟出方没有主牌时可以垫任意两张牌")
    else:
        print("❌ 第二轮中，跟出方垫牌被错误拒绝")
        all_correct = False
    
    print("\n" + "="*70)
    if all_correct:
        print("所有验证通过！✓")
    else:
        print("存在错误！❌")
    print("="*70)


if __name__ == "__main__":
    test_consecutive_rounds()

