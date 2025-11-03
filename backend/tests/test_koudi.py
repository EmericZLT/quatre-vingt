import os, sys
CURRENT_DIR = os.path.dirname(__file__)
BACKEND_DIR = os.path.abspath(os.path.join(CURRENT_DIR, ".."))
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)
from app.models.game import Card, Suit, Rank, PlayerPosition
from app.game.card_playing import CardPlayingSystem
from app.game.card_system import CardSystem

def card(suit, rank, is_joker=False):
    return Card(suit=suit, rank=rank, is_joker=is_joker)

def test_koudi_single():
    """测试抠底-最后一墩为单牌"""
    card_system = CardSystem()
    sys = CardPlayingSystem(card_system, trump_suit=Suit.HEARTS)
    sys.set_idle_positions([PlayerPosition.EAST, PlayerPosition.WEST])
    sys.set_bottom_cards([
        card(Suit.HEARTS, Rank.FIVE),  # 5分
        card(Suit.CLUBS, Rank.TEN),    # 10分
        card(Suit.SPADES, Rank.KING),  # 10分
    ])  # 总底25
    # 四家都空，模拟最后一墩由East获胜
    sys.all_players_hands = {
        PlayerPosition.EAST: [],
        PlayerPosition.WEST: [],
        PlayerPosition.NORTH: [],
        PlayerPosition.SOUTH: []
    }
    # 当前圈：先放3家，最后一手作为第4出牌触发结算；均为单牌
    sys.trick_leader = PlayerPosition.EAST
    sys.led_cards = [card(Suit.HEARTS, Rank.FOUR)]
    sys.current_trick = [
        (PlayerPosition.EAST, [card(Suit.HEARTS, Rank.FOUR)]),
        (PlayerPosition.SOUTH, [card(Suit.HEARTS, Rank.TWO)]),
        (PlayerPosition.WEST, [card(Suit.HEARTS, Rank.THREE)])
    ]
    sys._determine_trick_winner = lambda: PlayerPosition.EAST
    # 第四家出牌
    res = sys._follow_cards(PlayerPosition.NORTH, [card(Suit.HEARTS, Rank.SIX)], [])
    print(f"[TEST] 抠底-单牌：idle_score={sys.idle_score}")
    assert sys.idle_score == 50

def test_koudi_pair():
    """测试抠底-最后一墩为对子"""
    card_system = CardSystem()
    sys = CardPlayingSystem(card_system, trump_suit=Suit.HEARTS)
    sys.set_idle_positions([PlayerPosition.EAST, PlayerPosition.WEST])
    sys.set_bottom_cards([
        card(Suit.CLUBS, Rank.TEN), card(Suit.CLUBS, Rank.TEN)
    ])  # 总20分
    sys.all_players_hands = {
        PlayerPosition.EAST: [], PlayerPosition.WEST: [], PlayerPosition.NORTH: [], PlayerPosition.SOUTH: []
    }
    # 当前圈：对子（避免使用5/10/K，防止本墩自身得分干扰）
    sys.trick_leader = PlayerPosition.EAST
    sys.led_cards = [card(Suit.HEARTS, Rank.SEVEN), card(Suit.HEARTS, Rank.SEVEN)]
    sys.current_trick = [
        (PlayerPosition.EAST, [card(Suit.HEARTS, Rank.SEVEN), card(Suit.HEARTS, Rank.SEVEN)]),
        (PlayerPosition.SOUTH, [card(Suit.HEARTS, Rank.SIX), card(Suit.HEARTS, Rank.SIX)]),
        (PlayerPosition.WEST, [card(Suit.HEARTS, Rank.FOUR), card(Suit.HEARTS, Rank.FOUR)])
    ]
    sys._determine_trick_winner = lambda: PlayerPosition.EAST
    res = sys._follow_cards(PlayerPosition.NORTH, [card(Suit.HEARTS, Rank.THREE), card(Suit.HEARTS, Rank.THREE)], [])
    print(f"[TEST] 抠底-对子：idle_score={sys.idle_score}")
    assert sys.idle_score == 80

def test_koudi_tractor():
    """测试抠底-最后一墩为连对（2连对）"""
    card_system = CardSystem()
    sys = CardPlayingSystem(card_system, trump_suit=Suit.HEARTS)
    sys.set_idle_positions([PlayerPosition.EAST, PlayerPosition.WEST])
    sys.set_bottom_cards([
        card(Suit.CLUBS, Rank.KING), card(Suit.CLUBS, Rank.KING),
        card(Suit.HEARTS, Rank.FIVE), card(Suit.HEARTS, Rank.FIVE)
    ])  # 底分30
    sys.all_players_hands = {
        PlayerPosition.EAST: [], PlayerPosition.WEST: [], PlayerPosition.NORTH: [], PlayerPosition.SOUTH: []
    }
    # 当前圈：用非计分点数组成拖拉机（如 8-7 连对）
    sys.trick_leader = PlayerPosition.EAST
    led = [card(Suit.CLUBS, Rank.EIGHT), card(Suit.CLUBS, Rank.EIGHT), card(Suit.CLUBS, Rank.SEVEN), card(Suit.CLUBS, Rank.SEVEN)]
    sys.led_cards = led
    sys.current_trick = [
        (PlayerPosition.EAST, led),
        (PlayerPosition.SOUTH, [card(Suit.CLUBS, Rank.SIX), card(Suit.CLUBS, Rank.SIX), card(Suit.CLUBS, Rank.FOUR), card(Suit.CLUBS, Rank.FOUR)]),
        (PlayerPosition.WEST, [card(Suit.CLUBS, Rank.THREE), card(Suit.CLUBS, Rank.THREE), card(Suit.CLUBS, Rank.TWO), card(Suit.CLUBS, Rank.TWO)])
    ]
    sys._determine_trick_winner = lambda: PlayerPosition.EAST
    res = sys._follow_cards(PlayerPosition.NORTH, [card(Suit.CLUBS, Rank.NINE), card(Suit.CLUBS, Rank.NINE), card(Suit.CLUBS, Rank.FIVE), card(Suit.CLUBS, Rank.FIVE)], [])
    print(f"[TEST] 抠底-连对：idle_score={sys.idle_score}")
    # 底分30 * 8 = 240，加上本墩两张5的10分，共250
    assert sys.idle_score == 250

def test_koudi_slingshot():
    """测试抠底-甩牌混合型最大判定（使用非计分点数作为甩牌）"""
    card_system = CardSystem()
    sys = CardPlayingSystem(card_system, trump_suit=Suit.HEARTS)
    sys.set_idle_positions([PlayerPosition.EAST, PlayerPosition.WEST])
    sys.set_bottom_cards([
        card(Suit.CLUBS, Rank.FIVE), card(Suit.CLUBS, Rank.KING), card(Suit.DIAMONDS, Rank.KING)
    ])  # 25
    sys.all_players_hands = {PlayerPosition.EAST: [], PlayerPosition.WEST: [], PlayerPosition.NORTH: [], PlayerPosition.SOUTH: []}
    # 领出为混合甩牌（包含一组连对 + 一组对子 + 单张），选择非计分点数
    sys.trick_leader = PlayerPosition.EAST
    led = [
        card(Suit.CLUBS, Rank.EIGHT), card(Suit.CLUBS, Rank.EIGHT),  # 对子一
        card(Suit.CLUBS, Rank.SEVEN), card(Suit.CLUBS, Rank.SEVEN),  # 对子二 -> 构成连对（2连）
        card(Suit.CLUBS, Rank.ACE), card(Suit.CLUBS, Rank.ACE),      # 额外一对
        card(Suit.DIAMONDS, Rank.SIX),                               # 单张
    ]
    sys.led_cards = led
    # 每家需出7张，S/W 用非计分牌避免额外分数（N 包含三张5制造+15）
    sys.current_trick = [
        (PlayerPosition.EAST, led),
        (PlayerPosition.SOUTH, [
            card(Suit.CLUBS, Rank.SIX), card(Suit.CLUBS, Rank.SIX),
            card(Suit.CLUBS, Rank.FOUR), card(Suit.CLUBS, Rank.FOUR),
            card(Suit.DIAMONDS, Rank.FOUR),
            card(Suit.CLUBS, Rank.ACE), card(Suit.CLUBS, Rank.ACE)
        ]),
        (PlayerPosition.WEST, [
            card(Suit.CLUBS, Rank.THREE), card(Suit.CLUBS, Rank.THREE),
            card(Suit.CLUBS, Rank.TWO), card(Suit.CLUBS, Rank.TWO),
            card(Suit.DIAMONDS, Rank.THREE),
            card(Suit.CLUBS, Rank.ACE), card(Suit.CLUBS, Rank.ACE)
        ])
    ]
    sys._determine_trick_winner = lambda: PlayerPosition.EAST
    # NORTH 出7张，包含三张5 -> 本墩+15；底分25 * 最大倍数8 = 200；合计215
    res = sys._follow_cards(PlayerPosition.NORTH, [
        card(Suit.CLUBS, Rank.NINE), card(Suit.CLUBS, Rank.NINE),
        card(Suit.CLUBS, Rank.FIVE), card(Suit.CLUBS, Rank.FIVE), card(Suit.DIAMONDS, Rank.FIVE),
        card(Suit.CLUBS, Rank.ACE), card(Suit.CLUBS, Rank.ACE)
    ], [])
    print(f"[TEST] 抠底-甩牌混合型最大判定：idle_score={sys.idle_score}")
    assert sys.idle_score == 215


def test_koudi_slingshot_single():
    """测试抠底-甩牌单牌最大判定（使用非计分点数作为甩牌）"""
    card_system = CardSystem()
    sys = CardPlayingSystem(card_system, trump_suit=Suit.HEARTS)
    sys.set_idle_positions([PlayerPosition.EAST, PlayerPosition.WEST])
    sys.set_bottom_cards([
        card(Suit.CLUBS, Rank.FIVE), card(Suit.CLUBS, Rank.KING), card(Suit.DIAMONDS, Rank.KING)
    ])  # 25
    sys.all_players_hands = {PlayerPosition.EAST: [], PlayerPosition.WEST: [], PlayerPosition.NORTH: [], PlayerPosition.SOUTH: []}
    # 领出为单牌甩牌，选择非计分点数
    sys.trick_leader = PlayerPosition.EAST
    led = [
        card(Suit.CLUBS, Rank.NINE), card(Suit.CLUBS, Rank.EIGHT),  
        card(Suit.CLUBS, Rank.SEVEN), card(Suit.CLUBS, Rank.FOUR), 
        card(Suit.DIAMONDS, Rank.SIX),  # 单
    ]
    sys.led_cards = led
    sys.current_trick = [
        (PlayerPosition.EAST, led),
        (PlayerPosition.SOUTH, [card(Suit.CLUBS, Rank.SIX), card(Suit.CLUBS, Rank.SIX), card(Suit.CLUBS, Rank.FOUR), card(Suit.CLUBS, Rank.FOUR), card(Suit.DIAMONDS, Rank.FOUR)]),
        (PlayerPosition.WEST, [card(Suit.CLUBS, Rank.THREE), card(Suit.CLUBS, Rank.THREE), card(Suit.CLUBS, Rank.TWO), card(Suit.CLUBS, Rank.TWO), card(Suit.DIAMONDS, Rank.THREE)])
    ]
    sys._determine_trick_winner = lambda: PlayerPosition.EAST
    res = sys._follow_cards(PlayerPosition.NORTH, [card(Suit.CLUBS, Rank.NINE), card(Suit.CLUBS, Rank.NINE), card(Suit.CLUBS, Rank.FIVE), card(Suit.CLUBS, Rank.FIVE), card(Suit.DIAMONDS, Rank.FIVE)], [])
    print(f"[TEST] 抠底-甩牌混合型最大判定：idle_score={sys.idle_score}")
    assert sys.idle_score == 65


if __name__ == "__main__":
    test_koudi_single()
    test_koudi_pair()
    test_koudi_tractor()
    test_koudi_slingshot()
    test_koudi_slingshot_single()
    print("✔ 抠底结算相关测试全部通过！\n")
