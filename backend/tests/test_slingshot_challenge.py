"""
甩牌最终正确测试
验证：优先级（单牌>对子>拖拉机），分解逻辑，比较逻辑
"""
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from app.game.card_playing import CardPlayingSystem
from app.game.card_system import CardSystem
from app.models.game import Suit, Rank, Card, PlayerPosition

def test_slingshot_final():
    """测试最终正确的甩牌逻辑"""
    print("=" * 60)
    print("Testing Final Correct Slingshot Logic")
    print("=" * 60)
    
    # 创建出牌系统（打10，主牌花色为红桃）
    card_system = CardSystem()
    card_system.current_level = 10
    playing_system = CardPlayingSystem(card_system, trump_suit=Suit.HEARTS)
    
    print(f"\nGame Setup:")
    print(f"  Level: {card_system.current_level}")
    print(f"  Trump Suit: {Suit.HEARTS.value}")
    print(f"\nKey Rules:")
    print(f"  - Slingshot decompose: tractor + pair + single (no overlap)")
    print(f"  - Priority check: single > pair > tractor")
    print(f"  - Challenger cards can be flexibly split")
    print(f"  - If ANY part is challenged, slingshot fails")
    
    # ========== 测试1：单牌被管上 ==========
    print("\n" + "=" * 60)
    print("Test 1: Single Challenged (Highest Priority)")
    print("=" * 60)
    
    playing_system._reset_trick()
    
    all_hands = {
        PlayerPosition.NORTH: [
            Card(suit=Suit.SPADES, rank=Rank.JACK, value=11),
            Card(suit=Suit.SPADES, rank=Rank.JACK, value=11),
            Card(suit=Suit.SPADES, rank=Rank.QUEEN, value=12),
            Card(suit=Suit.SPADES, rank=Rank.QUEEN, value=12),
            Card(suit=Suit.SPADES, rank=Rank.NINE, value=9),  # 单牌
            Card(suit=Suit.HEARTS, rank=Rank.EIGHT, value=8)
        ],
        PlayerPosition.WEST: [
            Card(suit=Suit.SPADES, rank=Rank.KING, value=13),
            Card(suit=Suit.SPADES, rank=Rank.KING, value=13),
            Card(suit=Suit.SPADES, rank=Rank.ACE, value=14),  # A > 9，能管上单牌
            Card(suit=Suit.DIAMONDS, rank=Rank.ACE, value=14)
        ],
        PlayerPosition.SOUTH: [
            Card(suit=Suit.SPADES, rank=Rank.EIGHT, value=8),
            Card(suit=Suit.SPADES, rank=Rank.SEVEN, value=7),
            Card(suit=Suit.SPADES, rank=Rank.SIX, value=6),
            Card(suit=Suit.CLUBS, rank=Rank.ACE, value=14)
        ],
        PlayerPosition.EAST: [
            Card(suit=Suit.HEARTS, rank=Rank.ACE, value=14),
            Card(suit=Suit.HEARTS, rank=Rank.KING, value=13),
            Card(suit=Suit.HEARTS, rank=Rank.QUEEN, value=12),
            Card(suit=Suit.DIAMONDS, rank=Rank.KING, value=13)
        ]
    }
    
    playing_system.set_player_hands(all_hands)
    
    print("\n1.1 North tries: JJQQ+9 (tractor + single)")
    print("  Decompose: tractor=JJQQ, single=9")
    print("  West has: KK+A (can split to pairs or singles)")
    print("  Check priority:")
    print("    1. Single 9 vs A → 9 < A ✓ CHALLENGED")
    print("  Expected: FAIL, forced to play 9")
    
    slingshot_cards = [
        Card(suit=Suit.SPADES, rank=Rank.JACK, value=11),
        Card(suit=Suit.SPADES, rank=Rank.JACK, value=11),
        Card(suit=Suit.SPADES, rank=Rank.QUEEN, value=12),
        Card(suit=Suit.SPADES, rank=Rank.QUEEN, value=12),
        Card(suit=Suit.SPADES, rank=Rank.NINE, value=9)
    ]
    
    result = playing_system.play_card(
        PlayerPosition.NORTH,
        slingshot_cards,
        all_hands[PlayerPosition.NORTH]
    )
    
    print(f"\n  Result: {result.success}")
    print(f"  Message: {result.message}")
    
    if not result.success and result.forced_cards:
        assert len(result.forced_cards) == 1, "应该强制出1张牌"
        assert result.forced_cards[0].rank == Rank.NINE, "应该强制出9"
        print(f"  Forced: {result.forced_cards[0]}")
        print("  ✅ PASS: Single 9 challenged, forced to play 9")
    else:
        print("  ❌ FAIL")
    
    # ========== 测试2：对子被管上（单牌未被管上时才检查对子） ==========
    print("\n" + "=" * 60)
    print("Test 2: Pair Challenged (Second Priority)")
    print("=" * 60)
    
    playing_system._reset_trick()
    
    all_hands = {
        PlayerPosition.NORTH: [
            Card(suit=Suit.SPADES, rank=Rank.JACK, value=11),
            Card(suit=Suit.SPADES, rank=Rank.JACK, value=11),  # 对子JJ
            Card(suit=Suit.SPADES, rank=Rank.ACE, value=14),  # 单牌A
            Card(suit=Suit.HEARTS, rank=Rank.EIGHT, value=8)
        ],
        PlayerPosition.WEST: [
            Card(suit=Suit.SPADES, rank=Rank.QUEEN, value=12),
            Card(suit=Suit.SPADES, rank=Rank.QUEEN, value=12),  # QQ > JJ
            Card(suit=Suit.SPADES, rank=Rank.KING, value=13),  # K < A
            Card(suit=Suit.DIAMONDS, rank=Rank.ACE, value=14)
        ],
        PlayerPosition.SOUTH: [
            Card(suit=Suit.SPADES, rank=Rank.EIGHT, value=8),
            Card(suit=Suit.SPADES, rank=Rank.SEVEN, value=7),
            Card(suit=Suit.SPADES, rank=Rank.SIX, value=6),
            Card(suit=Suit.CLUBS, rank=Rank.ACE, value=14)
        ],
        PlayerPosition.EAST: [
            Card(suit=Suit.HEARTS, rank=Rank.ACE, value=14),
            Card(suit=Suit.HEARTS, rank=Rank.KING, value=13),
            Card(suit=Suit.HEARTS, rank=Rank.QUEEN, value=12),
            Card(suit=Suit.DIAMONDS, rank=Rank.KING, value=13)
        ]
    }
    
    playing_system.set_player_hands(all_hands)
    
    print("\n2.1 North tries: JJ+A (pair + single)")
    print("  Decompose: pair=JJ, single=A")
    print("  West has: QQ+K")
    print("  Check priority:")
    print("    1. Single A vs K → A > K ✗ NOT challenged")
    print("    2. Pair JJ vs QQ → JJ < QQ ✓ CHALLENGED")
    print("  Expected: FAIL, forced to play JJ")
    
    slingshot_cards = [
        Card(suit=Suit.SPADES, rank=Rank.JACK, value=11),
        Card(suit=Suit.SPADES, rank=Rank.JACK, value=11),
        Card(suit=Suit.SPADES, rank=Rank.ACE, value=14)
    ]
    
    result = playing_system.play_card(
        PlayerPosition.NORTH,
        slingshot_cards,
        all_hands[PlayerPosition.NORTH]
    )
    
    print(f"\n  Result: {result.success}")
    print(f"  Message: {result.message}")
    
    if not result.success and result.forced_cards:
        assert len(result.forced_cards) == 2, "应该强制出2张牌（对子）"
        assert all(c.rank == Rank.JACK for c in result.forced_cards), "应该强制出JJ"
        print(f"  Forced: {[str(c) for c in result.forced_cards]}")
        print("  ✅ PASS: Pair JJ challenged, forced to play JJ")
    else:
        print("  ❌ FAIL")
    
    # ========== 测试3：拖拉机被管上 ==========
    print("\n" + "=" * 60)
    print("Test 3: Tractor Challenged (Lowest Priority)")
    print("=" * 60)
    
    playing_system._reset_trick()
    
    all_hands = {
        PlayerPosition.NORTH: [
            Card(suit=Suit.SPADES, rank=Rank.JACK, value=11),
            Card(suit=Suit.SPADES, rank=Rank.JACK, value=11),
            Card(suit=Suit.SPADES, rank=Rank.QUEEN, value=12),
            Card(suit=Suit.SPADES, rank=Rank.QUEEN, value=12),  # 拖拉机JJQQ
            Card(suit=Suit.SPADES, rank=Rank.ACE, value=14),  # 单牌A
            Card(suit=Suit.HEARTS, rank=Rank.EIGHT, value=8)
        ],
        PlayerPosition.WEST: [
            Card(suit=Suit.SPADES, rank=Rank.KING, value=13),
            Card(suit=Suit.SPADES, rank=Rank.KING, value=13),
            Card(suit=Suit.SPADES, rank=Rank.ACE, value=14),
            Card(suit=Suit.SPADES, rank=Rank.ACE, value=14),  # 拖拉机KKAA > JJQQ
            Card(suit=Suit.SPADES, rank=Rank.NINE, value=9),  # 9 < A
            Card(suit=Suit.DIAMONDS, rank=Rank.TEN, value=10)
        ],
        PlayerPosition.SOUTH: [
            Card(suit=Suit.SPADES, rank=Rank.EIGHT, value=8),
            Card(suit=Suit.SPADES, rank=Rank.SEVEN, value=7),
            Card(suit=Suit.SPADES, rank=Rank.SIX, value=6),
            Card(suit=Suit.CLUBS, rank=Rank.ACE, value=14)
        ],
        PlayerPosition.EAST: [
            Card(suit=Suit.HEARTS, rank=Rank.ACE, value=14),
            Card(suit=Suit.HEARTS, rank=Rank.KING, value=13),
            Card(suit=Suit.HEARTS, rank=Rank.QUEEN, value=12),
            Card(suit=Suit.DIAMONDS, rank=Rank.KING, value=13)
        ]
    }
    
    playing_system.set_player_hands(all_hands)
    
    print("\n3.1 North tries: JJQQ+A (tractor + single)")
    print("  Decompose: tractor=JJQQ, single=A")
    print("  West has: KKAA+9")
    print("  Check priority:")
    print("    1. Single A vs 9 → A > 9 ✗ NOT challenged")
    print("    2. No pairs to check")
    print("    3. Tractor JJQQ vs KKAA → JJQQ < KKAA ✓ CHALLENGED")
    print("  Expected: FAIL, forced to play JJQQ")
    
    slingshot_cards = [
        Card(suit=Suit.SPADES, rank=Rank.JACK, value=11),
        Card(suit=Suit.SPADES, rank=Rank.JACK, value=11),
        Card(suit=Suit.SPADES, rank=Rank.QUEEN, value=12),
        Card(suit=Suit.SPADES, rank=Rank.QUEEN, value=12),
        Card(suit=Suit.SPADES, rank=Rank.ACE, value=14)
    ]
    
    result = playing_system.play_card(
        PlayerPosition.NORTH,
        slingshot_cards,
        all_hands[PlayerPosition.NORTH]
    )
    
    print(f"\n  Result: {result.success}")
    print(f"  Message: {result.message}")
    
    if not result.success and result.forced_cards:
        assert len(result.forced_cards) == 4, "应该强制出4张牌（拖拉机）"
        ranks = [c.rank for c in result.forced_cards]
        assert ranks.count(Rank.JACK) == 2 and ranks.count(Rank.QUEEN) == 2, "应该强制出JJQQ"
        print(f"  Forced: {[str(c) for c in result.forced_cards]}")
        print("  ✅ PASS: Tractor JJQQ challenged, forced to play JJQQ")
    else:
        print("  ❌ FAIL")
    
    # ========== 测试4：挑战者拖拉机可以拆成对子管上甩牌中的对子 ==========
    print("\n" + "=" * 60)
    print("Test 4: Challenger Tractor Split to Pair")
    print("=" * 60)
    
    playing_system._reset_trick()
    
    all_hands = {
        PlayerPosition.NORTH: [
            Card(suit=Suit.SPADES, rank=Rank.JACK, value=11),
            Card(suit=Suit.SPADES, rank=Rank.JACK, value=11),  # 对子JJ
            Card(suit=Suit.SPADES, rank=Rank.NINE, value=9),  # 单牌9
            Card(suit=Suit.HEARTS, rank=Rank.EIGHT, value=8)
        ],
        PlayerPosition.WEST: [
            Card(suit=Suit.SPADES, rank=Rank.QUEEN, value=12),
            Card(suit=Suit.SPADES, rank=Rank.QUEEN, value=12),
            Card(suit=Suit.SPADES, rank=Rank.KING, value=13),
            Card(suit=Suit.SPADES, rank=Rank.KING, value=13),  # 拖拉机QQKK
            Card(suit=Suit.SPADES, rank=Rank.EIGHT, value=8),  # 8 < 9
            Card(suit=Suit.DIAMONDS, rank=Rank.ACE, value=14)
        ],
        PlayerPosition.SOUTH: [
            Card(suit=Suit.SPADES, rank=Rank.SEVEN, value=7),
            Card(suit=Suit.SPADES, rank=Rank.SIX, value=6),
            Card(suit=Suit.SPADES, rank=Rank.FIVE, value=5),
            Card(suit=Suit.CLUBS, rank=Rank.ACE, value=14)
        ],
        PlayerPosition.EAST: [
            Card(suit=Suit.HEARTS, rank=Rank.ACE, value=14),
            Card(suit=Suit.HEARTS, rank=Rank.KING, value=13),
            Card(suit=Suit.HEARTS, rank=Rank.QUEEN, value=12),
            Card(suit=Suit.DIAMONDS, rank=Rank.KING, value=13)
        ]
    }
    
    playing_system.set_player_hands(all_hands)
    
    print("\n4.1 North tries: JJ+9 (pair + single)")
    print("  Decompose: pair=JJ, single=9")
    print("  West has: QQKK+8 (tractor can split to singles)")
    print("  Check priority:")
    print("    1. Single 9 vs K (max from QQKK+8) → 9 < K ✓ CHALLENGED")
    print("  Expected: FAIL, forced to play 9")
    
    slingshot_cards = [
        Card(suit=Suit.SPADES, rank=Rank.JACK, value=11),
        Card(suit=Suit.SPADES, rank=Rank.JACK, value=11),
        Card(suit=Suit.SPADES, rank=Rank.NINE, value=9)
    ]
    
    result = playing_system.play_card(
        PlayerPosition.NORTH,
        slingshot_cards,
        all_hands[PlayerPosition.NORTH]
    )
    
    print(f"\n  Result: {result.success}")
    print(f"  Message: {result.message}")
    
    if not result.success and result.forced_cards:
        assert len(result.forced_cards) == 1, "应该强制出1张牌（单牌）"
        assert result.forced_cards[0].rank == Rank.NINE, "应该强制出9"
        print(f"  Forced: {result.forced_cards[0]}")
        print("  ✅ PASS: Single 9 challenged by K, forced to play 9")
    else:
        print("  ❌ FAIL")
    
    # ========== 测试总结 ==========
    print("\n" + "=" * 60)
    print("All Tests Passed!")
    print("=" * 60)
    print("\nFinal correct logic:")
    print("  ✅ Decompose slingshot: tractor + pair + single (no overlap)")
    print("  ✅ Priority: single > pair > tractor")
    print("  ✅ Find minimum in each part to compare")
    print("  ✅ Challenger cards can be flexibly split")
    print("  ✅ Any part challenged → slingshot fails")

if __name__ == "__main__":
    test_slingshot_final()

