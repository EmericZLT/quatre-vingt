"""
测试对子拆分规则
验证在甩牌场景下，是否可以拆对子
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.models.game import Card, Suit, Rank, PlayerPosition
from app.game.card_system import CardSystem
from app.game.card_playing import CardPlayingSystem


def create_card(suit: Suit, rank: Rank) -> Card:
    """创建卡牌的辅助函数"""
    return Card(suit=suit, rank=rank)


def test_pair_splitting_in_slingshot():
    """
    测试甩牌场景下的对子拆分
    
    场景：
    - 领出方甩牌：AAK（2个A + 1个K）
    - 跟出方手牌：JJ66（2个J + 2个6）
    - 跟出方应该可以出：J66 或 JJ6（拆对子）
    """
    print("\n" + "="*70)
    print("测试甩牌场景下的对子拆分")
    print("="*70)
    
    card_system = CardSystem()
    card_system.current_level = 2  # 级别2，避免与测试牌冲突
    trump_suit = Suit.HEARTS  # 红心为主
    card_playing = CardPlayingSystem(card_system, trump_suit)
    
    # 领出方甩牌：黑桃AAK
    led_cards = [
        create_card(Suit.SPADES, Rank.ACE),
        create_card(Suit.SPADES, Rank.ACE),
        create_card(Suit.SPADES, Rank.KING),
    ]
    
    # 领出方手牌（包含甩牌）
    leader_hand = led_cards.copy()
    
    # 跟出方手牌：黑桃JJ66
    follower_hand = [
        create_card(Suit.SPADES, Rank.JACK),
        create_card(Suit.SPADES, Rank.JACK),
        create_card(Suit.SPADES, Rank.SIX),
        create_card(Suit.SPADES, Rank.SIX),
    ]
    
    # 设置所有玩家手牌（用于甩牌验证）
    card_playing.set_player_hands({
        PlayerPosition.NORTH: leader_hand,
        PlayerPosition.EAST: follower_hand,
        PlayerPosition.SOUTH: [create_card(Suit.CLUBS, Rank.THREE)],  # 无黑桃
        PlayerPosition.WEST: [create_card(Suit.CLUBS, Rank.FOUR)],    # 无黑桃
    })
    
    # 领出甩牌
    print("\n1. 领出方甩牌：黑桃AAK（2个A + 1个K）")
    lead_result = card_playing.play_card(
        PlayerPosition.NORTH,
        led_cards,
        leader_hand
    )
    print(f"   甩牌结果: {lead_result.success}, {lead_result.message}")
    
    if not lead_result.success:
        print(f"   ❌ 甩牌失败，无法继续测试")
        return
    
    # 跟出方尝试1：J66（拆JJ对子）
    print("\n2. 跟出方尝试1：黑桃J66（拆JJ对子，保留66对子）")
    follow_cards_1 = [
        create_card(Suit.SPADES, Rank.JACK),
        create_card(Suit.SPADES, Rank.SIX),
        create_card(Suit.SPADES, Rank.SIX),
    ]
    follow_result_1 = card_playing.play_card(
        PlayerPosition.EAST,
        follow_cards_1,
        follower_hand
    )
    print(f"   跟牌结果: {follow_result_1.success}, {follow_result_1.message}")
    
    if follow_result_1.success:
        print("   ✓ 正确：可以拆对子来凑够数量")
    else:
        print(f"   ❌ 错误：应该允许拆对子")
    
    # 重置trick以便测试第二次尝试
    card_playing._reset_trick()
    card_playing.play_card(PlayerPosition.NORTH, led_cards, leader_hand)
    
    # 跟出方尝试2：JJ6（拆66对子）
    print("\n3. 跟出方尝试2：黑桃JJ6（保留JJ对子，拆66对子）")
    follow_cards_2 = [
        create_card(Suit.SPADES, Rank.JACK),
        create_card(Suit.SPADES, Rank.JACK),
        create_card(Suit.SPADES, Rank.SIX),
    ]
    follow_result_2 = card_playing.play_card(
        PlayerPosition.EAST,
        follow_cards_2,
        follower_hand
    )
    print(f"   跟牌结果: {follow_result_2.success}, {follow_result_2.message}")
    
    if follow_result_2.success:
        print("   ✓ 正确：可以拆对子来凑够数量")
    else:
        print(f"   ❌ 错误：应该允许拆对子")
    
    print("\n" + "="*70)
    print("验证结果：")
    print("="*70)
    
    if follow_result_1.success and follow_result_2.success:
        print("✓ 所有测试通过！在甩牌场景下可以拆对子")
    else:
        print("❌ 存在错误！")
        if not follow_result_1.success:
            print(f"   - 尝试1失败: {follow_result_1.message}")
        if not follow_result_2.success:
            print(f"   - 尝试2失败: {follow_result_2.message}")
    print("="*70)


def test_pair_must_follow_pair():
    """
    测试对子跟对子的规则（不应该被破坏）
    
    场景：
    - 领出方出对子：AA
    - 跟出方手牌：JJ66
    - 跟出方必须出对子（不能出J6）
    """
    print("\n" + "="*70)
    print("测试对子跟对子规则（确保没有被破坏）")
    print("="*70)
    
    card_system = CardSystem()
    card_system.current_level = 2
    trump_suit = Suit.HEARTS
    card_playing = CardPlayingSystem(card_system, trump_suit)
    
    # 领出方出对子：黑桃AA
    led_cards = [
        create_card(Suit.SPADES, Rank.ACE),
        create_card(Suit.SPADES, Rank.ACE),
    ]
    
    leader_hand = led_cards.copy()
    
    # 跟出方手牌：黑桃JJ66
    follower_hand = [
        create_card(Suit.SPADES, Rank.JACK),
        create_card(Suit.SPADES, Rank.JACK),
        create_card(Suit.SPADES, Rank.SIX),
        create_card(Suit.SPADES, Rank.SIX),
    ]
    
    # 领出对子
    print("\n1. 领出方出对子：黑桃AA")
    lead_result = card_playing.play_card(
        PlayerPosition.NORTH,
        led_cards,
        leader_hand
    )
    print(f"   领出结果: {lead_result.success}, {lead_result.message}")
    
    # 跟出方尝试：J6（拆对子，应该被拒绝）
    print("\n2. 跟出方尝试：黑桃J6（拆对子）")
    follow_cards = [
        create_card(Suit.SPADES, Rank.JACK),
        create_card(Suit.SPADES, Rank.SIX),
    ]
    follow_result = card_playing.play_card(
        PlayerPosition.EAST,
        follow_cards,
        follower_hand
    )
    print(f"   跟牌结果: {follow_result.success}, {follow_result.message}")
    
    print("\n" + "="*70)
    print("验证结果：")
    print("="*70)
    
    if not follow_result.success:
        print("✓ 正确：领出对子时，跟出方必须出对子（不能拆对子）")
    else:
        print("❌ 错误：领出对子时，应该拒绝拆对子的跟牌")
    print("="*70)


if __name__ == "__main__":
    test_pair_splitting_in_slingshot()
    test_pair_must_follow_pair()
    print("\n测试完成！")

