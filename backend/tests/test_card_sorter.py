"""
测试：手牌排序功能
"""
import os
import sys

# 允许脚本直跑
CURRENT_DIR = os.path.dirname(__file__)
BACKEND_DIR = os.path.abspath(os.path.join(CURRENT_DIR, ".."))
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from app.models.game import Card, Suit, Rank
from app.game.card_sorter import CardSorter


def _make_card(suit: Suit, rank: Rank, is_joker: bool = False) -> Card:
    """创建一张牌"""
    return Card(suit=suit, rank=rank, is_joker=is_joker)


def test_basic_sorting_no_trump():
    """测试基本排序（未定主）"""
    sorter = CardSorter(current_level=2, trump_suit=None)
    
    # 创建一些牌：大王、小王、级牌2♠、级牌2♥、副牌K♠、副牌A♥、副牌5♣
    cards = [
        _make_card(Suit.HEARTS, Rank.ACE, is_joker=True),  # 小王
        _make_card(Suit.SPADES, Rank.ACE, is_joker=True),  # 大王
        _make_card(Suit.HEARTS, Rank.TWO),  # 级牌2♥
        _make_card(Suit.SPADES, Rank.TWO),  # 级牌2♠
        _make_card(Suit.SPADES, Rank.KING),  # 副牌K♠
        _make_card(Suit.HEARTS, Rank.ACE),  # 副牌A♥
        _make_card(Suit.CLUBS, Rank.FIVE),  # 副牌5♣
    ]
    
    sorted_cards = sorter.sort_cards(cards)
    
    # 验证顺序：大王 → 小王 → 级牌2♠ → 级牌2♥ → 副牌K♠ → 副牌A♥ → 副牌5♣
    assert sorted_cards[0].is_joker and sorted_cards[0].suit == Suit.SPADES, "第一个应该是大王"
    assert sorted_cards[1].is_joker and sorted_cards[1].suit == Suit.HEARTS, "第二个应该是小王"
    assert sorted_cards[2].rank == Rank.TWO and sorted_cards[2].suit == Suit.SPADES, "第三个应该是级牌2♠"
    assert sorted_cards[3].rank == Rank.TWO and sorted_cards[3].suit == Suit.HEARTS, "第四个应该是级牌2♥"
    assert sorted_cards[4].suit == Suit.SPADES and sorted_cards[4].rank == Rank.KING, "第五个应该是K♠"
    assert sorted_cards[5].suit == Suit.HEARTS and sorted_cards[5].rank == Rank.ACE, "第六个应该是A♥"
    assert sorted_cards[6].suit == Suit.CLUBS and sorted_cards[6].rank == Rank.FIVE, "第七个应该是5♣"
    
    print("[测试1] 基本排序（未定主）通过 ✓")


def test_sorting_with_trump():
    """测试定主后的排序（红心为主）"""
    sorter = CardSorter(current_level=2, trump_suit=Suit.HEARTS)
    
    # 创建牌：级牌2♠、级牌2♥、主牌花色的K♥、A♥、副牌K♠、5♣
    cards = [
        _make_card(Suit.HEARTS, Rank.TWO),  # 级牌2♥
        _make_card(Suit.SPADES, Rank.TWO),  # 级牌2♠
        _make_card(Suit.HEARTS, Rank.KING),  # 主牌K♥
        _make_card(Suit.HEARTS, Rank.ACE),  # 主牌A♥
        _make_card(Suit.SPADES, Rank.KING),  # 副牌K♠
        _make_card(Suit.CLUBS, Rank.FIVE),  # 副牌5♣
    ]
    
    sorted_cards = sorter.sort_cards(cards)
    
    # 验证顺序：级牌2♠ → 级牌2♥ → 主牌A♥ → 主牌K♥ → 副牌K♠ → 副牌5♣
    # 注意：定主后，主牌花色的非级牌移到副牌最左侧
    assert sorted_cards[0].rank == Rank.TWO and sorted_cards[0].suit == Suit.SPADES, "第一个应该是级牌2♠"
    assert sorted_cards[1].rank == Rank.TWO and sorted_cards[1].suit == Suit.HEARTS, "第二个应该是级牌2♥"
    assert sorted_cards[2].suit == Suit.HEARTS and sorted_cards[2].rank == Rank.ACE, "第三个应该是主牌A♥（移到副牌最左侧）"
    assert sorted_cards[3].suit == Suit.HEARTS and sorted_cards[3].rank == Rank.KING, "第四个应该是主牌K♥（移到副牌最左侧）"
    assert sorted_cards[4].suit == Suit.SPADES and sorted_cards[4].rank == Rank.KING, "第五个应该是副牌K♠"
    assert sorted_cards[5].suit == Suit.CLUBS and sorted_cards[5].rank == Rank.FIVE, "第六个应该是副牌5♣"
    
    print("[测试2] 定主后排序（红心为主）通过 ✓")


def test_sorting_with_clubs_trump():
    """测试梅花为主牌时的特殊排序规则"""
    sorter = CardSorter(current_level=2, trump_suit=Suit.CLUBS)
    
    # 创建牌：级牌2♠、级牌2♣、主牌K♣、副牌K♠、副牌A♥、副牌5♦
    cards = [
        _make_card(Suit.SPADES, Rank.TWO),  # 级牌2♠
        _make_card(Suit.CLUBS, Rank.TWO),  # 级牌2♣
        _make_card(Suit.CLUBS, Rank.KING),  # 主牌K♣
        _make_card(Suit.SPADES, Rank.KING),  # 副牌K♠
        _make_card(Suit.HEARTS, Rank.ACE),  # 副牌A♥
        _make_card(Suit.DIAMONDS, Rank.FIVE),  # 副牌5♦
    ]
    
    sorted_cards = sorter.sort_cards(cards)
    
    # 验证顺序：级牌2♠ → 级牌2♣ → 主牌K♣ → 副牌A♥ → 副牌K♠ → 副牌5♦
    # 特殊规则：梅花为主时，副牌顺序为 ♥ → ♠ → ♦（黑桃排到红心后面）
    # 注意：主牌花色的非级牌移到副牌最左侧
    assert sorted_cards[0].rank == Rank.TWO and sorted_cards[0].suit == Suit.SPADES, "第一个应该是级牌2♠"
    assert sorted_cards[1].rank == Rank.TWO and sorted_cards[1].suit == Suit.CLUBS, "第二个应该是级牌2♣"
    assert sorted_cards[2].suit == Suit.CLUBS and sorted_cards[2].rank == Rank.KING, "第三个应该是主牌K♣（移到副牌最左侧）"
    assert sorted_cards[3].suit == Suit.HEARTS and sorted_cards[3].rank == Rank.ACE, "第四个应该是副牌A♥（黑桃排到红心后面）"
    assert sorted_cards[4].suit == Suit.SPADES and sorted_cards[4].rank == Rank.KING, "第五个应该是副牌K♠"
    assert sorted_cards[5].suit == Suit.DIAMONDS and sorted_cards[5].rank == Rank.FIVE, "第六个应该是副牌5♦"
    
    print("[测试3] 梅花为主牌时的特殊排序通过 ✓")


def test_same_suit_ordering():
    """测试相同花色的牌从大到小排序"""
    sorter = CardSorter(current_level=2, trump_suit=None)
    
    # 创建同一花色的多张牌
    cards = [
        _make_card(Suit.SPADES, Rank.THREE),
        _make_card(Suit.SPADES, Rank.ACE),
        _make_card(Suit.SPADES, Rank.FIVE),
    ]
    
    sorted_cards = sorter.sort_cards(cards)
    
    # 验证从大到小：A → 5 → 3
    assert sorted_cards[0].rank == Rank.ACE, "第一张应该是A"
    assert sorted_cards[1].rank == Rank.FIVE, "第二张应该是5"
    assert sorted_cards[2].rank == Rank.THREE, "第三张应该是3"
    
    print("[测试4] 相同花色从大到小排序通过 ✓")


def test_full_sorting_example():
    """测试完整排序示例"""
    sorter = CardSorter(current_level=5, trump_suit=Suit.SPADES)
    
    # 创建完整的牌组：大王、级牌5♥、级牌5♠、主牌K♠、主牌A♠、副牌K♥、副牌5♣
    cards = [
        _make_card(Suit.HEARTS, Rank.ACE, is_joker=True),  # 小王
        _make_card(Suit.SPADES, Rank.ACE, is_joker=True),  # 大王
        _make_card(Suit.HEARTS, Rank.FIVE),  # 级牌5♥
        _make_card(Suit.SPADES, Rank.FIVE),  # 级牌5♠
        _make_card(Suit.SPADES, Rank.KING),  # 主牌K♠
        _make_card(Suit.SPADES, Rank.ACE),  # 主牌A♠
        _make_card(Suit.HEARTS, Rank.KING),  # 副牌K♥
        _make_card(Suit.CLUBS, Rank.FIVE),  # 副牌5♣
    ]
    
    sorted_cards = sorter.sort_cards(cards)
    
    # 验证顺序
    card_strs = [str(c) for c in sorted_cards]
    print(f"[测试5] 完整排序结果: {' → '.join(card_strs)}")
    
    # 验证结构：大王 → 小王 → 级牌5♠ → 级牌5♥ → 主牌A♠ → 主牌K♠ → 副牌K♥ → 副牌5♣
    assert sorted_cards[0].is_joker and sorted_cards[0].suit == Suit.SPADES, "应该是大王"
    assert sorted_cards[1].is_joker and sorted_cards[1].suit == Suit.HEARTS, "应该是小王"
    assert sorted_cards[2].rank == Rank.FIVE and sorted_cards[2].suit == Suit.SPADES, "应该是级牌5♠"
    assert sorted_cards[3].rank == Rank.FIVE and sorted_cards[3].suit == Suit.HEARTS, "应该是级牌5♥"
    assert sorted_cards[4].rank == Rank.ACE and sorted_cards[4].suit == Suit.SPADES, "应该是主牌A♠（移到副牌最左侧）"
    assert sorted_cards[5].rank == Rank.KING and sorted_cards[5].suit == Suit.SPADES, "应该是主牌K♠（移到副牌最左侧）"
    
    print("[测试5] 完整排序示例通过 ✓")


def demo_manual_check_sort():
    """
    使用GameState逐张发牌流程，随机主花色、级牌，展示四家+底牌的排序结果。
    """
    import random
    from app.models.game import GameRoom, Player, PlayerPosition
    from app.game.game_state import GameState
    from app.game.card_sorter import CardSorter

    level = random.randint(2, 14)
    trump_suit = random.choice([Suit.SPADES, Suit.HEARTS, Suit.CLUBS, Suit.DIAMONDS])
    # 构造玩家和room
    players = []
    for pos, name in zip(
        [PlayerPosition.NORTH, PlayerPosition.WEST, PlayerPosition.SOUTH, PlayerPosition.EAST],
        ['North', 'West', 'South', 'East']
    ):
        players.append(Player(id=name, name=name, position=pos))
    room = GameRoom(id="room1", name="测试房间", players=players)
    game_state = GameState(room)
    # 设置主级并洗牌
    game_state.card_system.set_level(level)
    game_state.trump_suit = trump_suit
    game_state.room.trump_suit = trump_suit
    # 强制满足can_start条件
    for p in game_state.room.players:
        p.is_ready = True
    game_state.room.status = 'PLAYING'
    # 开始游戏发牌
    game_state.start_game()
    # 依次一张一张发牌
    for _ in range(100):
        game_state.deal_tick()
    # 各家排序并展示
    print("\n随机演示——级牌:%s, 主牌:%s" % (level, trump_suit.value))
    for pos in [PlayerPosition.NORTH, PlayerPosition.WEST, PlayerPosition.SOUTH, PlayerPosition.EAST]:
        player = game_state.get_player_by_position(pos)
        sorter = CardSorter(current_level=level, trump_suit=trump_suit)
        sorted_cards = sorter.sort_cards(player.cards)
        card_strs = [str(c) for c in sorted_cards]
        print(f"{pos.value.title()} 排序后手牌: {' '.join(card_strs)}")
    # 底牌
    sorter = CardSorter(current_level=level, trump_suit=trump_suit)
    sorted_bottom = sorter.sort_cards(list(game_state.bottom_cards))
    card_strs = [str(c) for c in sorted_bottom]
    print(f"Bottom 排序后手牌: {' '.join(card_strs)}")
    print("---请人工核查花色、主副牌、级牌、王牌顺序和底牌合理性（逐张发牌）---\n")


if __name__ == "__main__":
    print("==== 开始运行手牌排序测试 ====")
    
    test_cases = [
        ("test_basic_sorting_no_trump", test_basic_sorting_no_trump),
        ("test_sorting_with_trump", test_sorting_with_trump),
        ("test_sorting_with_clubs_trump", test_sorting_with_clubs_trump),
        ("test_same_suit_ordering", test_same_suit_ordering),
        ("test_full_sorting_example", test_full_sorting_example),
    ]
    
    for name, test_func in test_cases:
        try:
            test_func()
            print(f"[{name}] PASS\n")
        except AssertionError as e:
            print(f"[{name}] FAIL: {e}\n")
    # 新增：人工判断排序演示
    demo_manual_check_sort()
    print("==== 所有测试完成 ====")

