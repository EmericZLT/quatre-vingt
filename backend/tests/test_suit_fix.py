"""
测试花色判断修复
验证级牌在出牌阶段被正确识别为主牌
"""
from app.models.game import Card, Suit, Rank
from app.game.card_system import CardSystem
from app.game.card_playing import CardPlayingSystem

def test_level_card_as_trump():
    """测试级牌被正确识别为主牌"""
    print("=" * 60)
    print("测试：级牌在出牌阶段被正确识别为主牌")
    print("=" * 60)
    
    # 创建卡牌系统，当前级别为2
    card_system = CardSystem()
    card_system.current_level = 2
    
    # 创建出牌系统，主牌花色为红桃
    trump_suit = Suit.HEARTS
    card_playing = CardPlayingSystem(card_system, trump_suit)
    
    # 测试各种牌的花色识别
    test_cases = [
        # (牌, 期望的花色类型, 描述)
        (Card(suit=Suit.SPADES, rank=Rank.TWO), "trump", "黑桃2（级牌）应该是主牌"),
        (Card(suit=Suit.DIAMONDS, rank=Rank.TWO), "trump", "方块2（级牌）应该是主牌"),
        (Card(suit=Suit.CLUBS, rank=Rank.TWO), "trump", "梅花2（级牌）应该是主牌"),
        (Card(suit=Suit.HEARTS, rank=Rank.TWO), "trump", "红桃2（级牌+主花色）应该是主牌"),
        (Card(suit=Suit.HEARTS, rank=Rank.THREE), "trump", "红桃3（主花色）应该是主牌"),
        (Card(suit=Suit.SPADES, rank=Rank.THREE), Suit.SPADES.value, "黑桃3（副牌）应该是黑桃"),
        (Card(rank=Rank.BIG_JOKER, is_joker=True), "trump", "大王应该是主牌"),
        (Card(rank=Rank.SMALL_JOKER, is_joker=True), "trump", "小王应该是主牌"),
    ]
    
    all_passed = True
    for card, expected_suit, description in test_cases:
        actual_suit = card_playing._get_card_suit(card)
        if actual_suit == expected_suit:
            print(f"✓ {description}")
            print(f"  {card} -> {actual_suit}")
        else:
            print(f"✗ {description}")
            print(f"  {card} -> 期望: {expected_suit}, 实际: {actual_suit}")
            all_passed = False
    
    print()
    print("=" * 60)
    if all_passed:
        print("✓ 所有测试通过！")
    else:
        print("✗ 部分测试失败")
    print("=" * 60)
    
    return all_passed

def test_slingshot_with_level_cards():
    """测试甩牌时级牌被正确识别"""
    print("\n" + "=" * 60)
    print("测试：甩牌时级牌被正确识别为同一花色")
    print("=" * 60)
    
    # 创建卡牌系统，当前级别为2
    card_system = CardSystem()
    card_system.current_level = 2
    
    # 创建出牌系统，主牌花色为红桃
    trump_suit = Suit.HEARTS
    card_playing = CardPlayingSystem(card_system, trump_suit)
    
    # 测试甩牌识别
    test_cases = [
        # (牌列表, 是否应该识别为甩牌, 描述)
        (
            [
                Card(suit=Suit.SPADES, rank=Rank.TWO),
                Card(suit=Suit.DIAMONDS, rank=Rank.TWO),
                Card(suit=Suit.HEARTS, rank=Rank.THREE)
            ],
            True,
            "三张级牌和主花色牌应该识别为主牌甩牌"
        ),
        (
            [
                Card(suit=Suit.SPADES, rank=Rank.THREE),
                Card(suit=Suit.SPADES, rank=Rank.FOUR)
            ],
            True,
            "两张黑桃副牌应该识别为黑桃甩牌"
        ),
        (
            [
                Card(suit=Suit.SPADES, rank=Rank.TWO),
                Card(suit=Suit.SPADES, rank=Rank.THREE)
            ],
            False,
            "级牌和副牌混合不应该识别为甩牌（一个是主牌，一个是黑桃）"
        ),
    ]
    
    all_passed = True
    for cards, expected_is_slingshot, description in test_cases:
        actual_is_slingshot = card_playing._is_slingshot(cards)
        if actual_is_slingshot == expected_is_slingshot:
            print(f"✓ {description}")
            print(f"  {[str(c) for c in cards]} -> {actual_is_slingshot}")
        else:
            print(f"✗ {description}")
            print(f"  {[str(c) for c in cards]} -> 期望: {expected_is_slingshot}, 实际: {actual_is_slingshot}")
            all_passed = False
    
    print()
    print("=" * 60)
    if all_passed:
        print("✓ 所有测试通过！")
    else:
        print("✗ 部分测试失败")
    print("=" * 60)
    
    return all_passed

if __name__ == "__main__":
    result1 = test_level_card_as_trump()
    result2 = test_slingshot_with_level_cards()
    
    print("\n" + "=" * 60)
    print("总体测试结果")
    print("=" * 60)
    if result1 and result2:
        print("✓ 所有测试通过！级牌在出牌阶段被正确识别为主牌。")
    else:
        print("✗ 部分测试失败，请检查代码。")
    print("=" * 60)

