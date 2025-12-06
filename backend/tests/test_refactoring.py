"""
重构测试脚本
测试TrumpHelper重构后的功能是否正常
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.models.game import Card, Suit, Rank, PlayerPosition
from app.game.card_system import CardSystem
from app.game.trump_helper import TrumpHelper
from app.game.card_playing import CardPlayingSystem
from app.game.slingshot_logic import SlingshotLogic
from app.game.card_sorter import CardSorter
from app.game.card_comparison import CardComparison


def print_section(title):
    """打印分隔线"""
    print("\n" + "=" * 70)
    print(title)
    print("=" * 70)


def test_trump_helper():
    """测试TrumpHelper类的基本功能"""
    print_section("测试1: TrumpHelper基本功能")
    
    card_system = CardSystem()
    card_system.current_level = 2
    trump_suit = Suit.HEARTS
    helper = TrumpHelper(card_system, trump_suit)
    
    test_cases = [
        (Card(suit=Suit.SPADES, rank=Rank.TWO), True, "黑桃2（级牌）"),
        (Card(suit=Suit.HEARTS, rank=Rank.TWO), True, "红桃2（级牌+主花色）"),
        (Card(suit=Suit.HEARTS, rank=Rank.THREE), True, "红桃3（主花色）"),
        (Card(suit=Suit.SPADES, rank=Rank.THREE), False, "黑桃3（副牌）"),
        (Card(rank=Rank.BIG_JOKER, is_joker=True), True, "大王"),
        (Card(rank=Rank.SMALL_JOKER, is_joker=True), True, "小王"),
    ]
    
    all_passed = True
    for card, expected_is_trump, description in test_cases:
        is_trump = helper.is_trump(card)
        suit_type = helper.get_card_suit(card)
        
        if is_trump == expected_is_trump:
            print(f"✓ {description}: is_trump={is_trump}, suit_type={suit_type}")
        else:
            print(f"✗ {description}: 期望={expected_is_trump}, 实际={is_trump}")
            all_passed = False
    
    return all_passed


def test_trump_helper_filter():
    """测试TrumpHelper的筛选功能"""
    print_section("测试2: TrumpHelper筛选功能")
    
    card_system = CardSystem()
    card_system.current_level = 2
    trump_suit = Suit.HEARTS
    helper = TrumpHelper(card_system, trump_suit)
    
    cards = [
        Card(suit=Suit.SPADES, rank=Rank.TWO),      # 级牌（主牌）
        Card(suit=Suit.HEARTS, rank=Rank.THREE),    # 主花色（主牌）
        Card(suit=Suit.SPADES, rank=Rank.THREE),    # 副牌
        Card(suit=Suit.DIAMONDS, rank=Rank.FOUR),   # 副牌
        Card(rank=Rank.BIG_JOKER, is_joker=True),   # 大王（主牌）
    ]
    
    trump_cards = helper.filter_by_suit(cards, "trump")
    spade_cards = helper.filter_by_suit(cards, Suit.SPADES.value)
    
    print(f"总牌数: {len(cards)}")
    print(f"主牌数: {len(trump_cards)} (期望3)")
    print(f"黑桃副牌数: {len(spade_cards)} (期望1)")
    print(f"所有牌是否同花色: {helper.are_all_same_suit(cards)} (期望False)")
    print(f"主牌是否同花色: {helper.are_all_same_suit(trump_cards)} (期望True)")
    
    all_passed = (
        len(trump_cards) == 3 and
        len(spade_cards) == 1 and
        not helper.are_all_same_suit(cards) and
        helper.are_all_same_suit(trump_cards)
    )
    
    if all_passed:
        print("✓ 所有筛选测试通过")
    else:
        print("✗ 部分筛选测试失败")
    
    return all_passed


def test_card_playing_system():
    """测试CardPlayingSystem使用TrumpHelper后的功能"""
    print_section("测试3: CardPlayingSystem集成")
    
    card_system = CardSystem()
    card_system.current_level = 2
    trump_suit = Suit.HEARTS
    
    playing_system = CardPlayingSystem(card_system, trump_suit)
    
    # 测试领出牌
    player = PlayerPosition.NORTH
    cards = [Card(suit=Suit.SPADES, rank=Rank.TWO)]  # 级牌
    player_hand = [
        Card(suit=Suit.SPADES, rank=Rank.TWO),
        Card(suit=Suit.SPADES, rank=Rank.THREE),
        Card(suit=Suit.HEARTS, rank=Rank.FOUR),
    ]
    
    result = playing_system.play_card(player, cards, player_hand)
    
    print(f"领出级牌: {result.success}")
    print(f"领出花色类型: {playing_system.led_suit} (期望'trump')")
    
    all_passed = result.success and playing_system.led_suit == "trump"
    
    if all_passed:
        print("✓ CardPlayingSystem集成测试通过")
    else:
        print("✗ CardPlayingSystem集成测试失败")
    
    return all_passed


def test_slingshot_logic():
    """测试SlingshotLogic使用TrumpHelper后的功能"""
    print_section("测试4: SlingshotLogic集成")
    
    card_system = CardSystem()
    card_system.current_level = 2
    trump_suit = Suit.HEARTS
    
    slingshot = SlingshotLogic(card_system, trump_suit)
    
    # 测试主牌甩牌
    trump_cards = [
        Card(suit=Suit.SPADES, rank=Rank.TWO),      # 级牌
        Card(suit=Suit.DIAMONDS, rank=Rank.TWO),    # 级牌
        Card(suit=Suit.HEARTS, rank=Rank.THREE),    # 主花色
    ]
    
    player_hand = trump_cards + [
        Card(suit=Suit.SPADES, rank=Rank.FOUR),
        Card(suit=Suit.CLUBS, rank=Rank.FIVE),
    ]
    
    result = slingshot.validate_slingshot(trump_cards, player_hand)
    
    print(f"主牌甩牌验证: {result.is_valid}")
    print(f"原因: {result.reason if not result.is_valid else '有效'}")
    
    # 测试混合花色甩牌（应该失败）
    mixed_cards = [
        Card(suit=Suit.SPADES, rank=Rank.TWO),      # 级牌（主牌）
        Card(suit=Suit.SPADES, rank=Rank.FOUR),     # 黑桃（副牌）
    ]
    
    result2 = slingshot.validate_slingshot(mixed_cards, player_hand)
    
    print(f"混合花色甩牌验证: {result2.is_valid} (期望False)")
    
    all_passed = not result2.is_valid  # 混合花色应该失败
    
    if all_passed:
        print("✓ SlingshotLogic集成测试通过")
    else:
        print("✗ SlingshotLogic集成测试失败")
    
    return all_passed


def test_card_sorter():
    """测试CardSorter使用TrumpHelper后的功能"""
    print_section("测试5: CardSorter集成")
    
    sorter = CardSorter(current_level=2, trump_suit=Suit.HEARTS)
    
    cards = [
        Card(suit=Suit.SPADES, rank=Rank.THREE),    # 副牌
        Card(suit=Suit.SPADES, rank=Rank.TWO),      # 级牌（主牌）
        Card(suit=Suit.HEARTS, rank=Rank.FOUR),     # 主花色（主牌）
        Card(rank=Rank.BIG_JOKER, is_joker=True),   # 大王（主牌）
    ]
    
    trump_count = sum(1 for c in cards if sorter.is_trump_card(c))
    plain_count = sum(1 for c in cards if sorter.is_plain_suit_card(c))
    
    print(f"总牌数: {len(cards)}")
    print(f"主牌数: {trump_count} (期望3)")
    print(f"副牌数: {plain_count} (期望1)")
    
    sorted_cards = sorter.sort_cards(cards)
    print(f"排序后: {[str(c) for c in sorted_cards]}")
    
    all_passed = trump_count == 3 and plain_count == 1
    
    if all_passed:
        print("✓ CardSorter集成测试通过")
    else:
        print("✗ CardSorter集成测试失败")
    
    return all_passed


def test_card_comparison():
    """测试CardComparison使用TrumpHelper后的功能"""
    print_section("测试6: CardComparison集成")
    
    card_system = CardSystem()
    card_system.current_level = 2
    trump_suit = Suit.HEARTS
    
    comparison = CardComparison(card_system, trump_suit)
    
    # 级牌应该比普通主牌大
    level_card = Card(suit=Suit.SPADES, rank=Rank.TWO)  # 级牌
    trump_card = Card(suit=Suit.HEARTS, rank=Rank.ACE)  # 主花色A
    
    result = comparison.compare_cards(level_card, trump_card)
    
    print(f"级牌 vs 主花色A: {result} (期望1，表示级牌更大)")
    
    # 主牌应该比副牌大
    trump_card2 = Card(suit=Suit.HEARTS, rank=Rank.THREE)  # 主花色3
    plain_card = Card(suit=Suit.SPADES, rank=Rank.ACE)     # 副牌A
    
    result2 = comparison.compare_cards(trump_card2, plain_card)
    
    print(f"主花色3 vs 副牌A: {result2} (期望1，表示主牌更大)")
    
    all_passed = result == 1 and result2 == 1
    
    if all_passed:
        print("✓ CardComparison集成测试通过")
    else:
        print("✗ CardComparison集成测试失败")
    
    return all_passed


def test_level_card_suit_recognition():
    """测试级牌在不同场景下的花色识别"""
    print_section("测试7: 级牌花色识别（核心修复验证）")
    
    card_system = CardSystem()
    card_system.current_level = 2
    trump_suit = Suit.HEARTS
    helper = TrumpHelper(card_system, trump_suit)
    
    # 创建不同花色的级牌
    level_cards = [
        (Card(suit=Suit.SPADES, rank=Rank.TWO), "trump", "黑桃2"),
        (Card(suit=Suit.HEARTS, rank=Rank.TWO), "trump", "红桃2"),
        (Card(suit=Suit.DIAMONDS, rank=Rank.TWO), "trump", "方块2"),
        (Card(suit=Suit.CLUBS, rank=Rank.TWO), "trump", "梅花2"),
    ]
    
    all_passed = True
    print("所有级牌都应该被识别为主牌（'trump'）：")
    for card, expected_suit, description in level_cards:
        actual_suit = helper.get_card_suit(card)
        if actual_suit == expected_suit:
            print(f"✓ {description}: {actual_suit}")
        else:
            print(f"✗ {description}: 期望={expected_suit}, 实际={actual_suit}")
            all_passed = False
    
    # 测试级牌甩牌
    print("\n测试多张级牌是否被识别为同一花色：")
    all_level_cards = [card for card, _, _ in level_cards]
    is_same_suit = helper.are_all_same_suit(all_level_cards)
    print(f"所有级牌是否同花色: {is_same_suit} (期望True)")
    
    all_passed = all_passed and is_same_suit
    
    if all_passed:
        print("\n✓ 级牌花色识别测试通过")
    else:
        print("\n✗ 级牌花色识别测试失败")
    
    return all_passed


def main():
    """运行所有测试"""
    print("\n" + "=" * 70)
    print("重构测试 - TrumpHelper统一主副牌判断逻辑")
    print("=" * 70)
    
    results = []
    
    results.append(("TrumpHelper基本功能", test_trump_helper()))
    results.append(("TrumpHelper筛选功能", test_trump_helper_filter()))
    results.append(("CardPlayingSystem集成", test_card_playing_system()))
    results.append(("SlingshotLogic集成", test_slingshot_logic()))
    results.append(("CardSorter集成", test_card_sorter()))
    results.append(("CardComparison集成", test_card_comparison()))
    results.append(("级牌花色识别", test_level_card_suit_recognition()))
    
    print_section("测试总结")
    
    passed_count = sum(1 for _, passed in results if passed)
    total_count = len(results)
    
    for test_name, passed in results:
        status = "✓ 通过" if passed else "✗ 失败"
        print(f"{status}: {test_name}")
    
    print(f"\n总计: {passed_count}/{total_count} 测试通过")
    
    if passed_count == total_count:
        print("\n" + "=" * 70)
        print("🎉 所有测试通过！重构成功！")
        print("=" * 70)
        print("\n重构总结：")
        print("1. 创建了TrumpHelper类，统一管理主副牌判断逻辑")
        print("2. 消除了_get_card_suit方法的重复代码")
        print("3. 修复了级牌在出牌阶段被错误识别为副牌的问题")
        print("4. 优化了CardPlayingSystem、SlingshotLogic、CardSorter、CardComparison")
        print("5. 提高了代码的可维护性和职责清晰度")
    else:
        print("\n" + "=" * 70)
        print("⚠️ 部分测试失败，请检查代码")
        print("=" * 70)


if __name__ == "__main__":
    main()

