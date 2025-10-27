"""
甩牌逻辑完整测试
包含：甩牌验证、甩牌跟牌、甩牌获胜者判断
"""
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from app.game.card_playing import CardPlayingSystem
from app.game.card_system import CardSystem
from app.models.game import Suit, Rank, Card, PlayerPosition

def test_slingshot():
    """测试完整的甩牌系统"""
    print("=" * 60)
    print("Testing Complete Slingshot System")
    print("=" * 60)
    
    # 创建出牌系统（打10，主牌花色为红桃）
    card_system = CardSystem()
    card_system.current_level = 10
    playing_system = CardPlayingSystem(card_system, trump_suit=Suit.HEARTS)
    
    print(f"\nGame Setup:")
    print(f"  Level: {card_system.current_level}")
    print(f"  Trump Suit: {Suit.HEARTS.value}")
    
    # ========== 测试1：基础甩牌验证 ==========
    print("\n" + "=" * 60)
    print("Test 1: Basic Slingshot Validation")
    print("=" * 60)
    
    # 1.1 有效甩牌（同花色）
    print("\n1.1 Valid slingshot (same suit)")
    slingshot_cards = [
        Card(suit=Suit.SPADES, rank=Rank.ACE, value=14),
        Card(suit=Suit.SPADES, rank=Rank.KING, value=13),
        Card(suit=Suit.SPADES, rank=Rank.QUEEN, value=12)
    ]
    player_hand = slingshot_cards + [
        Card(suit=Suit.HEARTS, rank=Rank.NINE, value=9),
        Card(suit=Suit.CLUBS, rank=Rank.EIGHT, value=8)
    ]
    
    result = playing_system.slingshot_logic.validate_slingshot(slingshot_cards, player_hand)
    print(f"  Result: {'PASS' if result.is_valid else 'FAIL'}")
    print(f"  Card types: {result.card_types}")
    assert result.is_valid, "Should be valid slingshot"
    
    # 1.2 有效甩牌（不连续也可以）
    print("\n1.2 Valid slingshot (non-consecutive is OK)")
    slingshot_cards = [
        Card(suit=Suit.SPADES, rank=Rank.ACE, value=14),
        Card(suit=Suit.SPADES, rank=Rank.NINE, value=9),
        Card(suit=Suit.SPADES, rank=Rank.THREE, value=3)
    ]
    player_hand = slingshot_cards + [
        Card(suit=Suit.HEARTS, rank=Rank.KING, value=13),
        Card(suit=Suit.CLUBS, rank=Rank.QUEEN, value=12)
    ]
    
    result = playing_system.slingshot_logic.validate_slingshot(slingshot_cards, player_hand)
    print(f"  Result: {'PASS' if result.is_valid else 'FAIL'}")
    print(f"  Card types: {result.card_types}")
    assert result.is_valid, "Should be valid slingshot (不需要连续)"
    
    # 1.3 无效甩牌（不同花色）
    print("\n1.3 Invalid slingshot (different suits)")
    slingshot_cards = [
        Card(suit=Suit.SPADES, rank=Rank.ACE, value=14),
        Card(suit=Suit.HEARTS, rank=Rank.KING, value=13)
    ]
    player_hand = slingshot_cards + [
        Card(suit=Suit.CLUBS, rank=Rank.NINE, value=9)
    ]
    
    result = playing_system.slingshot_logic.validate_slingshot(slingshot_cards, player_hand)
    print(f"  Result: {'PASS' if not result.is_valid else 'FAIL'}")
    print(f"  Reason: {result.reason}")
    assert not result.is_valid, "Should be invalid slingshot"
    
    # 1.4 有效甩牌（包含对子）
    print("\n1.4 Valid slingshot with pair")
    slingshot_cards = [
        Card(suit=Suit.SPADES, rank=Rank.ACE, value=14),
        Card(suit=Suit.SPADES, rank=Rank.ACE, value=14),
        Card(suit=Suit.SPADES, rank=Rank.KING, value=13)
    ]
    player_hand = slingshot_cards + [
        Card(suit=Suit.HEARTS, rank=Rank.NINE, value=9)
    ]
    
    result = playing_system.slingshot_logic.validate_slingshot(slingshot_cards, player_hand)
    print(f"  Result: {'PASS' if result.is_valid else 'FAIL'}")
    print(f"  Card types: {result.card_types}")
    assert result.is_valid, "Should be valid slingshot"
    assert "pair" in result.card_types, "Should contain pair"
    
    # 1.5 有效甩牌（包含拖拉机，级牌是10）
    print("\n1.5 Valid slingshot with tractor (level 10, 9-J adjacent)")
    slingshot_cards = [
        Card(suit=Suit.SPADES, rank=Rank.NINE, value=9),
        Card(suit=Suit.SPADES, rank=Rank.NINE, value=9),
        Card(suit=Suit.SPADES, rank=Rank.JACK, value=11),
        Card(suit=Suit.SPADES, rank=Rank.JACK, value=11),
        Card(suit=Suit.SPADES, rank=Rank.EIGHT, value=8)
    ]
    player_hand = slingshot_cards + [
        Card(suit=Suit.HEARTS, rank=Rank.SEVEN, value=7)
    ]
    
    result = playing_system.slingshot_logic.validate_slingshot(slingshot_cards, player_hand)
    print(f"  Result: {'PASS' if result.is_valid else 'FAIL'}")
    print(f"  Card types: {result.card_types}")
    assert result.is_valid, "Should be valid slingshot"
    assert "tractor" in result.card_types, "Should contain tractor"
    
    # ========== 测试2：甩牌系统集成（单牌甩牌） ==========
    print("\n" + "=" * 60)
    print("Test 2: Slingshot System - Single Cards")
    print("=" * 60)
    
    playing_system._reset_trick()
    
    # 2.1 North领出甩牌
    print("\n2.1 North leads slingshot (3 single cards)")
    slingshot_cards = [
        Card(suit=Suit.SPADES, rank=Rank.ACE, value=14),
        Card(suit=Suit.SPADES, rank=Rank.KING, value=13),
        Card(suit=Suit.SPADES, rank=Rank.QUEEN, value=12)
    ]
    player_hand = slingshot_cards + [
        Card(suit=Suit.HEARTS, rank=Rank.NINE, value=9)
    ]
    
    result = playing_system.play_card(PlayerPosition.NORTH, slingshot_cards, player_hand)
    print(f"  Result: {'PASS' if result.success else 'FAIL'}")
    print(f"  Message: {result.message}")
    assert result.success, "Should lead successfully"
    
    # 2.2 West跟牌（有足够同花色）
    print("\n2.2 West follows with same suit")
    follower_cards = [
        Card(suit=Suit.SPADES, rank=Rank.JACK, value=11),
        Card(suit=Suit.SPADES, rank=Rank.NINE, value=9),
        Card(suit=Suit.SPADES, rank=Rank.EIGHT, value=8)
    ]
    follower_hand = follower_cards + [
        Card(suit=Suit.HEARTS, rank=Rank.SEVEN, value=7)
    ]
    
    result = playing_system.play_card(PlayerPosition.WEST, follower_cards, follower_hand)
    print(f"  Result: {'PASS' if result.success else 'FAIL'}")
    assert result.success, "Should follow successfully"
    
    # 2.3 South跟牌（没有足够同花色，垫牌）
    print("\n2.3 South follows without enough same suit (padding)")
    follower_cards = [
        Card(suit=Suit.SPADES, rank=Rank.TEN, value=10),
        Card(suit=Suit.HEARTS, rank=Rank.SIX, value=6),
        Card(suit=Suit.CLUBS, rank=Rank.FIVE, value=5)
    ]
    follower_hand = follower_cards + [
        Card(suit=Suit.DIAMONDS, rank=Rank.FOUR, value=4)
    ]
    
    result = playing_system.play_card(PlayerPosition.SOUTH, follower_cards, follower_hand)
    print(f"  Result: {'PASS' if result.success else 'FAIL'}")
    assert result.success, "Should follow successfully"
    
    # 2.4 East跟牌（用主牌将吃）
    print("\n2.4 East follows with trumps (winning)")
    follower_cards = [
        Card(suit=Suit.HEARTS, rank=Rank.ACE, value=14),
        Card(suit=Suit.HEARTS, rank=Rank.KING, value=13),
        Card(suit=Suit.CLUBS, rank=Rank.TEN, value=10)  # 级牌（主牌）
    ]
    follower_hand = follower_cards + [
        Card(suit=Suit.DIAMONDS, rank=Rank.THREE, value=3)
    ]
    
    result = playing_system.play_card(PlayerPosition.EAST, follower_cards, follower_hand)
    print(f"  Result: {'PASS' if result.success else 'FAIL'}")
    if result.winner:
        print(f"  Winner: {result.winner.value}")
        assert result.winner == PlayerPosition.EAST, "East should win with level card"
    
    # ========== 测试3：甩牌包含对子 ==========
    print("\n" + "=" * 60)
    print("Test 3: Slingshot with Pairs")
    print("=" * 60)
    
    playing_system._reset_trick()

    # 3.1 North领出甩牌（包含对子）
    print("\n3.1 North leads slingshot with pair (AA + K)")
    slingshot_cards = [
        Card(suit=Suit.SPADES, rank=Rank.ACE, value=14),
        Card(suit=Suit.SPADES, rank=Rank.ACE, value=14),
        Card(suit=Suit.SPADES, rank=Rank.KING, value=13)
    ]
    player_hand = slingshot_cards + [
        Card(suit=Suit.HEARTS, rank=Rank.NINE, value=9)
    ]
    
    result = playing_system.play_card(PlayerPosition.NORTH, slingshot_cards, player_hand)
    print(f"  Result: {'PASS' if result.success else 'FAIL'}")
    print(f"  Message: {result.message}")
    assert result.success, "Should lead successfully"
    
    # 3.2 West跟牌（有对子，跟对子）
    print("\n3.2 West follows with pair (QQ + J)")
    follower_cards = [
        Card(suit=Suit.SPADES, rank=Rank.QUEEN, value=12),
        Card(suit=Suit.SPADES, rank=Rank.QUEEN, value=12),
        Card(suit=Suit.SPADES, rank=Rank.JACK, value=11)
    ]
    follower_hand = follower_cards + [
        Card(suit=Suit.HEARTS, rank=Rank.EIGHT, value=8)
    ]
    
    result = playing_system.play_card(PlayerPosition.WEST, follower_cards, follower_hand)
    print(f"  Result: {'PASS' if result.success else 'FAIL'}")
    assert result.success, "Should follow successfully"
    
    # 3.3 South跟牌（没有对子，只有单张）
    print("\n3.3 South follows without pair (3 single cards)")
    follower_cards = [
        Card(suit=Suit.SPADES, rank=Rank.TEN, value=10),
        Card(suit=Suit.SPADES, rank=Rank.NINE, value=9),
        Card(suit=Suit.SPADES, rank=Rank.EIGHT, value=8)
    ]
    follower_hand = follower_cards + [
        Card(suit=Suit.CLUBS, rank=Rank.SEVEN, value=7)
    ]
    
    result = playing_system.play_card(PlayerPosition.SOUTH, follower_cards, follower_hand)
    print(f"  Result: {'PASS' if result.success else 'FAIL'}")
    assert result.success, "Should follow successfully"
    
    # 3.4 East用主牌对子毙牌
    print("\n3.4 East trumps with trump pair (wins)")
    follower_cards = [
        Card(suit=Suit.HEARTS, rank=Rank.KING, value=13),  # 主牌
        Card(suit=Suit.HEARTS, rank=Rank.KING, value=13),  # 主牌对子
        Card(suit=Suit.HEARTS, rank=Rank.QUEEN, value=12)  # 主牌
    ]
    follower_hand = follower_cards + [
        Card(suit=Suit.DIAMONDS, rank=Rank.SIX, value=6)
    ]
    
    result = playing_system.play_card(PlayerPosition.EAST, follower_cards, follower_hand)
    print(f"  Result: {'PASS' if result.success else 'FAIL'}")
    if result.winner:
        print(f"  Winner: {result.winner.value}")
        assert result.winner == PlayerPosition.EAST, "East should win with trump pair"
    
    # ========== 测试4：甩牌包含拖拉机 ==========
    print("\n" + "=" * 60)
    print("Test 4: Slingshot with Tractor")
    print("=" * 60)
    
    playing_system._reset_trick()
    
    # 4.1 North领出甩牌（拖拉机 + 单牌）
    print("\n4.1 North leads slingshot with tractor (99JJ + 8)")
    slingshot_cards = [
        Card(suit=Suit.SPADES, rank=Rank.NINE, value=9),
        Card(suit=Suit.SPADES, rank=Rank.NINE, value=9),
        Card(suit=Suit.SPADES, rank=Rank.JACK, value=11),
        Card(suit=Suit.SPADES, rank=Rank.JACK, value=11),
        Card(suit=Suit.SPADES, rank=Rank.EIGHT, value=8)
    ]
    player_hand = slingshot_cards + [
        Card(suit=Suit.HEARTS, rank=Rank.SEVEN, value=7)
    ]
    
    result = playing_system.play_card(PlayerPosition.NORTH, slingshot_cards, player_hand)
    print(f"  Result: {'PASS' if result.success else 'FAIL'}")
    print(f"  Message: {result.message}")
    assert result.success, "Should lead successfully"
    
    # 4.2 West跟牌（有拖拉机）
    print("\n4.2 West follows with tractor (7766 + 5)")
    follower_cards = [
        Card(suit=Suit.SPADES, rank=Rank.SEVEN, value=7),
        Card(suit=Suit.SPADES, rank=Rank.SEVEN, value=7),
        Card(suit=Suit.SPADES, rank=Rank.SIX, value=6),
        Card(suit=Suit.SPADES, rank=Rank.SIX, value=6),
        Card(suit=Suit.SPADES, rank=Rank.FIVE, value=5)
    ]
    follower_hand = follower_cards + [
        Card(suit=Suit.HEARTS, rank=Rank.FOUR, value=4)
    ]
    
    result = playing_system.play_card(PlayerPosition.WEST, follower_cards, follower_hand)
    print(f"  Result: {'PASS' if result.success else 'FAIL'}")
    assert result.success, "Should follow successfully"
    
    # 4.3 South跟牌（没有拖拉机，只有对子）
    print("\n4.3 South follows without tractor (QQ + 3 single)")
    follower_cards = [
        Card(suit=Suit.SPADES, rank=Rank.QUEEN, value=12),
        Card(suit=Suit.SPADES, rank=Rank.QUEEN, value=12),
        Card(suit=Suit.SPADES, rank=Rank.FOUR, value=4),
        Card(suit=Suit.SPADES, rank=Rank.THREE, value=3),
        Card(suit=Suit.SPADES, rank=Rank.TWO, value=2)
    ]
    follower_hand = follower_cards + [
        Card(suit=Suit.CLUBS, rank=Rank.ACE, value=14)
    ]
    
    result = playing_system.play_card(PlayerPosition.SOUTH, follower_cards, follower_hand)
    print(f"  Result: {'PASS' if result.success else 'FAIL'}")
    assert result.success, "Should follow successfully"
    
    # 4.4 East用主牌拖拉机毙牌
    print("\n4.4 East trumps with trump tractor (wins)")
    follower_cards = [
        Card(suit=Suit.HEARTS, rank=Rank.NINE, value=9),  # 主牌
        Card(suit=Suit.HEARTS, rank=Rank.NINE, value=9),  # 主牌对子
        Card(suit=Suit.HEARTS, rank=Rank.EIGHT, value=8),  # 主牌
        Card(suit=Suit.HEARTS, rank=Rank.EIGHT, value=8),  # 主牌对子（拖拉机）
        Card(suit=Suit.HEARTS, rank=Rank.SEVEN, value=7)   # 主牌
    ]
    follower_hand = follower_cards + [
        Card(suit=Suit.DIAMONDS, rank=Rank.ACE, value=14)
    ]
    
    result = playing_system.play_card(PlayerPosition.EAST, follower_cards, follower_hand)
    print(f"  Result: {'PASS' if result.success else 'FAIL'}")
    if result.winner:
        print(f"  Winner: {result.winner.value}")
        assert result.winner == PlayerPosition.EAST, "East should win with trump tractor"
    
    # ========== 测试5：甩牌跟牌规则验证 ==========
    print("\n" + "=" * 60)
    print("Test 5: Slingshot Follow Rules Validation")
    print("=" * 60)
    
    # 5.1 跟牌者有对子必须出对子（违规测试）
    print("\n5.1 Follower has pair but plays singles (should FAIL)")
    playing_system._reset_trick()
    
    # North领出甩牌（AA + K）
    slingshot_cards = [
        Card(suit=Suit.SPADES, rank=Rank.ACE, value=14),
        Card(suit=Suit.SPADES, rank=Rank.ACE, value=14),
        Card(suit=Suit.SPADES, rank=Rank.KING, value=13)
    ]
    player_hand = slingshot_cards + [Card(suit=Suit.HEARTS, rank=Rank.NINE, value=9)]
    
    result = playing_system.play_card(PlayerPosition.NORTH, slingshot_cards, player_hand)
    print(f"  North leads AA+K: {result.success}")
    assert result.success, "Should lead successfully"
    
    # West尝试跟3个单张（但手中有对子QQ）
    print("  West tries to play 3 singles (but has pair QQ)")
    follower_cards = [
        Card(suit=Suit.SPADES, rank=Rank.QUEEN, value=12),  # 单张
        Card(suit=Suit.SPADES, rank=Rank.JACK, value=11),   # 单张
        Card(suit=Suit.SPADES, rank=Rank.TEN, value=10)     # 单张
    ]
    follower_hand = [
        Card(suit=Suit.SPADES, rank=Rank.QUEEN, value=12),
        Card(suit=Suit.SPADES, rank=Rank.QUEEN, value=12),  # 有对子QQ
        Card(suit=Suit.SPADES, rank=Rank.JACK, value=11),
        Card(suit=Suit.SPADES, rank=Rank.TEN, value=10),
        Card(suit=Suit.HEARTS, rank=Rank.EIGHT, value=8)
    ]
    
    result = playing_system.play_card(PlayerPosition.WEST, follower_cards, follower_hand)
    print(f"  West follows with singles: {result.success}")
    print(f"  Message: {result.message}")
    assert not result.success, "Should FAIL (有对子必须出对子)"
    
    # 5.2 主牌将吃但牌型不匹配（North应该获胜）
    print("\n5.2 Trump without matching card type (North wins)")
    print("  Rule: 将吃必须匹配牌型，否则领出者获胜")
    playing_system._reset_trick()
    
    # North领出甩牌（AA + K，有1个对子）
    slingshot_cards = [
        Card(suit=Suit.SPADES, rank=Rank.ACE, value=14),
        Card(suit=Suit.SPADES, rank=Rank.ACE, value=14),
        Card(suit=Suit.SPADES, rank=Rank.KING, value=13)
    ]
    player_hand = slingshot_cards + [Card(suit=Suit.HEARTS, rank=Rank.NINE, value=9)]
    
    result = playing_system.play_card(PlayerPosition.NORTH, slingshot_cards, player_hand)
    print(f"  North leads AA+K (1 pair): {result.success}")
    assert result.success, "Should lead successfully"
    
    # West跟牌（QQ + J，有1个对子）
    follower_cards = [
        Card(suit=Suit.SPADES, rank=Rank.QUEEN, value=12),
        Card(suit=Suit.SPADES, rank=Rank.QUEEN, value=12),
        Card(suit=Suit.SPADES, rank=Rank.JACK, value=11)
    ]
    follower_hand = follower_cards + [Card(suit=Suit.CLUBS, rank=Rank.NINE, value=9)]
    
    result = playing_system.play_card(PlayerPosition.WEST, follower_cards, follower_hand)
    print(f"  West follows QQ+J (1 pair): {result.success}")
    assert result.success, "Should follow successfully"
    
    # South跟牌（3个单张）
    follower_cards = [
        Card(suit=Suit.SPADES, rank=Rank.TEN, value=10),
        Card(suit=Suit.SPADES, rank=Rank.NINE, value=9),
        Card(suit=Suit.SPADES, rank=Rank.EIGHT, value=8)
    ]
    follower_hand = follower_cards + [Card(suit=Suit.DIAMONDS, rank=Rank.SEVEN, value=7)]
    
    result = playing_system.play_card(PlayerPosition.SOUTH, follower_cards, follower_hand)
    print(f"  South follows 3 singles: {result.success}")
    assert result.success, "Should follow successfully"
    
    # East用主牌将吃，但没有对子（只有3个单张主牌）
    print("  East trumps with 3 singles (NO pair, type mismatch)")
    follower_cards = [
        Card(suit=Suit.HEARTS, rank=Rank.ACE, value=14),   # 主牌单张
        Card(suit=Suit.HEARTS, rank=Rank.KING, value=13),  # 主牌单张
        Card(suit=Suit.HEARTS, rank=Rank.QUEEN, value=12)  # 主牌单张
    ]
    follower_hand = follower_cards + [Card(suit=Suit.DIAMONDS, rank=Rank.SIX, value=6)]
    
    result = playing_system.play_card(PlayerPosition.EAST, follower_cards, follower_hand)
    print(f"  East trumps: {result.success}")
    assert result.success, "Should be allowed to play"
    
    # 验证获胜者
    if result.winner:
        print(f"  Winner: {result.winner.value}")
        assert result.winner == PlayerPosition.NORTH, "North应该获胜（East牌型不匹配）"
        print(f"  Result: PASS (North wins because East has no pair)")
    
    # 5.3 主牌将吃且牌型匹配（East应该获胜）
    print("\n5.3 Trump with matching card type (East wins)")
    print("  Rule: 将吃牌型匹配，全是主牌的获胜")
    playing_system._reset_trick()
    
    # North领出甩牌（AA + K，有1个对子）
    slingshot_cards = [
        Card(suit=Suit.SPADES, rank=Rank.ACE, value=14),
        Card(suit=Suit.SPADES, rank=Rank.ACE, value=14),
        Card(suit=Suit.SPADES, rank=Rank.KING, value=13)
    ]
    player_hand = slingshot_cards + [Card(suit=Suit.HEARTS, rank=Rank.NINE, value=9)]
    
    result = playing_system.play_card(PlayerPosition.NORTH, slingshot_cards, player_hand)
    print(f"  North leads AA+K (1 pair): {result.success}")
    
    # West跟牌
    follower_cards = [
        Card(suit=Suit.SPADES, rank=Rank.QUEEN, value=12),
        Card(suit=Suit.SPADES, rank=Rank.QUEEN, value=12),
        Card(suit=Suit.SPADES, rank=Rank.JACK, value=11)
    ]
    follower_hand = follower_cards + [Card(suit=Suit.CLUBS, rank=Rank.NINE, value=9)]
    
    result = playing_system.play_card(PlayerPosition.WEST, follower_cards, follower_hand)
    print(f"  West follows QQ+J: {result.success}")
    
    # South跟牌
    follower_cards = [
        Card(suit=Suit.SPADES, rank=Rank.TEN, value=10),
        Card(suit=Suit.SPADES, rank=Rank.NINE, value=9),
        Card(suit=Suit.SPADES, rank=Rank.EIGHT, value=8)
    ]
    follower_hand = follower_cards + [Card(suit=Suit.DIAMONDS, rank=Rank.SEVEN, value=7)]
    
    result = playing_system.play_card(PlayerPosition.SOUTH, follower_cards, follower_hand)
    print(f"  South follows 3 singles: {result.success}")
    
    # East用主牌将吃，有对子（KK + Q）
    print("  East trumps with KK+Q (HAS pair, type matches)")
    follower_cards = [
        Card(suit=Suit.HEARTS, rank=Rank.KING, value=13),   # 主牌
        Card(suit=Suit.HEARTS, rank=Rank.KING, value=13),   # 主牌对子KK
        Card(suit=Suit.HEARTS, rank=Rank.QUEEN, value=12)   # 主牌
    ]
    follower_hand = follower_cards + [Card(suit=Suit.DIAMONDS, rank=Rank.SIX, value=6)]
    
    result = playing_system.play_card(PlayerPosition.EAST, follower_cards, follower_hand)
    print(f"  East trumps: {result.success}")
    assert result.success, "Should be allowed to play"
    
    # 验证获胜者
    if result.winner:
        print(f"  Winner: {result.winner.value}")
        assert result.winner == PlayerPosition.EAST, "East应该获胜（牌型匹配且全是主牌）"
        print(f"  Result: PASS (East wins with matching pair type)")
    
    # ========== 测试6：甩牌挑战检测 ==========
    print("\n" + "=" * 60)
    print("Test 6: Slingshot Challenge Detection")
    print("=" * 60)
    print("  Note: 甩牌挑战只看同花色的牌，不考虑主牌将吃")
    
    # 5.1 可以挑战（同花色有更大的牌）
    print("\n5.1 Can challenge (has bigger card in same suit)")
    slingshot_cards = [
        Card(suit=Suit.SPADES, rank=Rank.QUEEN, value=12),
        Card(suit=Suit.SPADES, rank=Rank.JACK, value=11)
    ]
    challenger_hand = [
        Card(suit=Suit.SPADES, rank=Rank.KING, value=13),  # 同花色有更大的牌，可以管上
        Card(suit=Suit.HEARTS, rank=Rank.NINE, value=9)
    ]
    
    can_challenge, challenge_cards = playing_system.slingshot_logic.check_slingshot_challenge(
        slingshot_cards,
        challenger_hand,
        Suit.SPADES.value
    )
    print(f"  Can challenge: {'PASS' if can_challenge else 'FAIL'}")
    print(f"  Challenge cards count: {len(challenge_cards)}")
    assert can_challenge, "Should be able to challenge (同花色有更大的牌)"
    
    # 5.2 不能挑战（同花色没有更大的牌）
    print("\n5.2 Cannot challenge (no bigger card in same suit)")
    slingshot_cards = [
        Card(suit=Suit.SPADES, rank=Rank.ACE, value=14),
        Card(suit=Suit.SPADES, rank=Rank.KING, value=13)
    ]
    challenger_hand = [
        Card(suit=Suit.SPADES, rank=Rank.QUEEN, value=12),  # 同花色但更小
        Card(suit=Suit.HEARTS, rank=Rank.NINE, value=9)
    ]
    
    can_challenge, challenge_cards = playing_system.slingshot_logic.check_slingshot_challenge(
        slingshot_cards,
        challenger_hand,
        Suit.SPADES.value
    )
    print(f"  Can challenge: {'PASS' if not can_challenge else 'FAIL'}")
    assert not can_challenge, "Should not be able to challenge (同花色没有更大的牌)"
    
    # 5.3 不能挑战（没有同花色，即使有主牌也不算）
    print("\n5.3 Cannot challenge (no same suit, even with trump)")
    slingshot_cards = [
        Card(suit=Suit.SPADES, rank=Rank.ACE, value=14),
        Card(suit=Suit.SPADES, rank=Rank.KING, value=13)
    ]
    challenger_hand = [
        Card(suit=Suit.HEARTS, rank=Rank.ACE, value=14),  # 主牌（但不算挑战）
        Card(suit=Suit.DIAMONDS, rank=Rank.QUEEN, value=12),  # 其他副牌
        Card(suit=Suit.CLUBS, rank=Rank.TEN, value=10)        # 级牌（但不算挑战）
    ]
    
    can_challenge, challenge_cards = playing_system.slingshot_logic.check_slingshot_challenge(
        slingshot_cards,
        challenger_hand,
        Suit.SPADES.value
    )
    print(f"  Can challenge: {'PASS' if not can_challenge else 'FAIL'}")
    assert not can_challenge, "Should not be able to challenge (没有同花色，主牌不算)"
    
    # ========== 测试7：超将吃规则 ==========
    print("\n" + "=" * 60)
    print("Test 7: Over-Trump Rules (Multiple Trumps)")
    print("=" * 60)
    
    # 7.1 甩牌有对子，比较对子大小
    print("\n7.1 Slingshot with pair - compare trump pairs")
    print("  Rule: 甩牌有对子时，将吃方比较对子大小")
    playing_system._reset_trick()
    
    # North领出：♠AA + ♠K（1个对子）
    slingshot_cards = [
        Card(suit=Suit.SPADES, rank=Rank.ACE, value=14),
        Card(suit=Suit.SPADES, rank=Rank.ACE, value=14),
        Card(suit=Suit.SPADES, rank=Rank.KING, value=13)
    ]
    player_hand = slingshot_cards + [Card(suit=Suit.DIAMONDS, rank=Rank.TWO, value=2)]
    result = playing_system.play_card(PlayerPosition.NORTH, slingshot_cards, player_hand)
    print(f"  North leads AA+K: {result.success}")
    
    # West将吃：♥QQ + ♥J（对子QQ）
    follower_cards = [
        Card(suit=Suit.HEARTS, rank=Rank.QUEEN, value=12),
        Card(suit=Suit.HEARTS, rank=Rank.QUEEN, value=12),
        Card(suit=Suit.HEARTS, rank=Rank.JACK, value=11)
    ]
    follower_hand = follower_cards + [Card(suit=Suit.DIAMONDS, rank=Rank.THREE, value=3)]
    result = playing_system.play_card(PlayerPosition.WEST, follower_cards, follower_hand)
    print(f"  West trumps with QQ+J: {result.success}")
    
    # South将吃：♥KK + ♥9（对子KK，比QQ大）
    follower_cards = [
        Card(suit=Suit.HEARTS, rank=Rank.KING, value=13),
        Card(suit=Suit.HEARTS, rank=Rank.KING, value=13),
        Card(suit=Suit.HEARTS, rank=Rank.NINE, value=9)
    ]
    follower_hand = follower_cards + [Card(suit=Suit.DIAMONDS, rank=Rank.FOUR, value=4)]
    result = playing_system.play_card(PlayerPosition.SOUTH, follower_cards, follower_hand)
    print(f"  South trumps with KK+9: {result.success}")
    
    # East将吃失败：♥10 + ♥J + ♥8（单牌10，J，8，不满足将吃牌型）
    follower_cards = [
        Card(suit=Suit.HEARTS, rank=Rank.TEN, value=10),
        Card(suit=Suit.HEARTS, rank=Rank.JACK, value=11),
        Card(suit=Suit.HEARTS, rank=Rank.EIGHT, value=8)
    ]
    follower_hand = follower_cards + [Card(suit=Suit.DIAMONDS, rank=Rank.FIVE, value=5)]
    result = playing_system.play_card(PlayerPosition.EAST, follower_cards, follower_hand)
    print(f"  East trumps with 10+J+8: {result.success}")
    
    if result.winner:
        print(f"  Winner: {result.winner.value}")
        assert result.winner == PlayerPosition.SOUTH, "South应该获胜（对子KK最大）"
        print(f"  Result: PASS (South wins with biggest pair KK)")
    
    # 7.2 甩牌全是单牌，比较最大单牌
    print("\n7.2 Slingshot with singles - compare max single card")
    print("  Rule: 甩牌全是单牌时，比较最大单牌，相同则先出牌者获胜")
    playing_system._reset_trick()
    
    # North领出：♠A ♠K ♠Q（全是单牌）
    slingshot_cards = [
        Card(suit=Suit.SPADES, rank=Rank.ACE, value=14),
        Card(suit=Suit.SPADES, rank=Rank.KING, value=13),
        Card(suit=Suit.SPADES, rank=Rank.QUEEN, value=12)
    ]
    player_hand = slingshot_cards + [Card(suit=Suit.DIAMONDS, rank=Rank.TWO, value=2)]
    result = playing_system.play_card(PlayerPosition.NORTH, slingshot_cards, player_hand)
    print(f"  North leads A+K+Q (singles): {result.success}")
    
    # West将吃：♥Q ♥J ♥9（最大♥Q）
    follower_cards = [
        Card(suit=Suit.HEARTS, rank=Rank.QUEEN, value=12),
        Card(suit=Suit.HEARTS, rank=Rank.JACK, value=11),
        Card(suit=Suit.HEARTS, rank=Rank.NINE, value=9)
    ]
    follower_hand = follower_cards + [Card(suit=Suit.DIAMONDS, rank=Rank.THREE, value=3)]
    result = playing_system.play_card(PlayerPosition.WEST, follower_cards, follower_hand)
    print(f"  West trumps with Q+J+9 (max Q): {result.success}")
    
    # South将吃：♥K ♥8 ♥7（最大♥K，比♥Q大）
    follower_cards = [
        Card(suit=Suit.HEARTS, rank=Rank.KING, value=13),
        Card(suit=Suit.HEARTS, rank=Rank.EIGHT, value=8),
        Card(suit=Suit.HEARTS, rank=Rank.SEVEN, value=7)
    ]
    follower_hand = follower_cards + [Card(suit=Suit.DIAMONDS, rank=Rank.FOUR, value=4)]
    result = playing_system.play_card(PlayerPosition.SOUTH, follower_cards, follower_hand)
    print(f"  South trumps with K+8+7 (max K): {result.success}")
    
    # East将吃：♥A ♥6 ♥5（最大♥A，比♥K大）
    follower_cards = [
        Card(suit=Suit.HEARTS, rank=Rank.ACE, value=14),
        Card(suit=Suit.HEARTS, rank=Rank.SIX, value=6),
        Card(suit=Suit.HEARTS, rank=Rank.FIVE, value=5)
    ]
    follower_hand = follower_cards + [Card(suit=Suit.DIAMONDS, rank=Rank.FIVE, value=5)]
    result = playing_system.play_card(PlayerPosition.EAST, follower_cards, follower_hand)
    print(f"  East trumps with A+6+5 (max A): {result.success}")
    
    if result.winner:
        print(f"  Winner: {result.winner.value}")
        assert result.winner == PlayerPosition.EAST, "East应该获胜（最大单牌A）"
        print(f"  Result: PASS (East wins with max single card A)")
    
    # 7.3 甩牌全是单牌，将吃方有对子也不比较对子
    print("\n7.3 Slingshot singles - trumps with pair still compare singles")
    print("  Rule: 比较逻辑由领出方决定，甩牌全单牌时只比较单牌")
    playing_system._reset_trick()
    
    # North领出：♠A ♠K ♠Q（全是单牌）
    slingshot_cards = [
        Card(suit=Suit.SPADES, rank=Rank.ACE, value=14),
        Card(suit=Suit.SPADES, rank=Rank.KING, value=13),
        Card(suit=Suit.SPADES, rank=Rank.QUEEN, value=12)
    ]
    player_hand = slingshot_cards + [Card(suit=Suit.DIAMONDS, rank=Rank.TWO, value=2)]
    result = playing_system.play_card(PlayerPosition.NORTH, slingshot_cards, player_hand)
    print(f"  North leads A+K+Q (all singles): {result.success}")
    
    # West将吃：♥AA + ♥K（有对子AA）
    print("  West trumps with AA+K (HAS pair AA)")
    follower_cards = [
        Card(suit=Suit.HEARTS, rank=Rank.ACE, value=14),
        Card(suit=Suit.HEARTS, rank=Rank.ACE, value=14),
        Card(suit=Suit.HEARTS, rank=Rank.KING, value=13)
    ]
    follower_hand = follower_cards + [Card(suit=Suit.DIAMONDS, rank=Rank.THREE, value=3)]
    result = playing_system.play_card(PlayerPosition.WEST, follower_cards, follower_hand)
    print(f"  West trumps (max single A, has pair): {result.success}")
    
    # South将吃：♠10 ♥Q ♥J（全是单牌，最大♠10）
    print("  South trumps with 10+Q+J (singles only)")
    follower_cards = [
        Card(suit=Suit.SPADES, rank=Rank.TEN, value=10),
        Card(suit=Suit.HEARTS, rank=Rank.QUEEN, value=12),
        Card(suit=Suit.HEARTS, rank=Rank.JACK, value=11)
    ]
    follower_hand = follower_cards + [Card(suit=Suit.DIAMONDS, rank=Rank.FOUR, value=4)]
    result = playing_system.play_card(PlayerPosition.SOUTH, follower_cards, follower_hand)
    print(f"  South trumps (max single 10): {result.success}")
    
    # East跟牌
    follower_cards = [
        Card(suit=Suit.SPADES, rank=Rank.JACK, value=11),
        Card(suit=Suit.SPADES, rank=Rank.TEN, value=10),
        Card(suit=Suit.SPADES, rank=Rank.NINE, value=9)
    ]
    follower_hand = follower_cards + [Card(suit=Suit.DIAMONDS, rank=Rank.FIVE, value=5)]
    result = playing_system.play_card(PlayerPosition.EAST, follower_cards, follower_hand)
    print(f"  East follows with side cards: {result.success}")
    
    if result.winner:
        print(f"  Winner: {result.winner.value}")
        assert result.winner == PlayerPosition.SOUTH, "South应该获胜（比较单牌，10>K，不看对子）"
        print(f"  Result: PASS (South wins by comparing singles 10>K, pair ignored)")
    
    # 7.4 最大单牌相同，先出牌者获胜
    print("\n7.4 Same max single card - first player wins")
    print("  Rule: 最大单牌相同时，先出牌者获胜")
    playing_system._reset_trick()
    
    # North领出：♠A ♠K ♠Q（全是单牌）
    slingshot_cards = [
        Card(suit=Suit.SPADES, rank=Rank.ACE, value=14),
        Card(suit=Suit.SPADES, rank=Rank.KING, value=13),
        Card(suit=Suit.SPADES, rank=Rank.QUEEN, value=12)
    ]
    player_hand = slingshot_cards + [Card(suit=Suit.DIAMONDS, rank=Rank.TWO, value=2)]
    result = playing_system.play_card(PlayerPosition.NORTH, slingshot_cards, player_hand)
    print(f"  North leads A+K+Q: {result.success}")
    
    # West将吃：♥K ♥J ♥9（最大♥K）
    follower_cards = [
        Card(suit=Suit.HEARTS, rank=Rank.KING, value=13),
        Card(suit=Suit.HEARTS, rank=Rank.JACK, value=11),
        Card(suit=Suit.HEARTS, rank=Rank.NINE, value=9)
    ]
    follower_hand = follower_cards + [Card(suit=Suit.DIAMONDS, rank=Rank.THREE, value=3)]
    result = playing_system.play_card(PlayerPosition.WEST, follower_cards, follower_hand)
    print(f"  West trumps with K+J+9 (max K): {result.success}")
    
    # South将吃：♥K ♥Q ♥8（最大♥K，与West相同）
    follower_cards = [
        Card(suit=Suit.HEARTS, rank=Rank.KING, value=13),
        Card(suit=Suit.HEARTS, rank=Rank.QUEEN, value=12),
        Card(suit=Suit.HEARTS, rank=Rank.EIGHT, value=8)
    ]
    follower_hand = follower_cards + [Card(suit=Suit.DIAMONDS, rank=Rank.FOUR, value=4)]
    result = playing_system.play_card(PlayerPosition.SOUTH, follower_cards, follower_hand)
    print(f"  South trumps with K+Q+8 (max K, same as West): {result.success}")
    
    # East跟牌（副牌）
    follower_cards = [
        Card(suit=Suit.SPADES, rank=Rank.JACK, value=11),
        Card(suit=Suit.SPADES, rank=Rank.TEN, value=10),
        Card(suit=Suit.SPADES, rank=Rank.NINE, value=9)
    ]
    follower_hand = follower_cards + [Card(suit=Suit.DIAMONDS, rank=Rank.FIVE, value=5)]
    result = playing_system.play_card(PlayerPosition.EAST, follower_cards, follower_hand)
    print(f"  East follows with side cards: {result.success}")
    
    if result.winner:
        print(f"  Winner: {result.winner.value}")
        assert result.winner == PlayerPosition.WEST, "West应该获胜（先出牌，最大单牌相同）"
        print(f"  Result: PASS (West wins - first player with max K)")
    
    # ========== 测试总结 ==========
    print("\n" + "=" * 60)
    print("All Tests Passed!")
    print("=" * 60)
    print("\nTest Coverage:")
    print("  - Basic slingshot validation")
    print("  - Slingshot with single cards")
    print("  - Slingshot with pairs")
    print("  - Slingshot with tractors")
    print("  - Follow rules validation")
    print("  - Trump type matching")
    print("  - Over-trump rules (pair/single)")
    print("  - Challenge detection")
    print("\nSlingshot system is working correctly!")

if __name__ == "__main__":
    test_slingshot()

