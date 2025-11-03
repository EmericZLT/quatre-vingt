"""
测试：闲家赢墩累计分数；非闲家赢墩不累计。
用例设计：
1) 第一墩：SOUTH(闲家)赢墩，墩内包含 5/10/K，共 25 分，应累计到闲家。
2) 第二墩：WEST(庄家阵营)赢墩，墩内也有分牌，但闲家分不增加。
"""
import os
import sys

# 确保可以以 `python backend/tests/test_scoring_idle.py` 直接运行
CURRENT_DIR = os.path.dirname(__file__)
BACKEND_DIR = os.path.abspath(os.path.join(CURRENT_DIR, ".."))
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from app.models.game import Card, Suit, Rank, PlayerPosition
from app.game.card_system import CardSystem
from app.game.card_playing import CardPlayingSystem


def _make_card(s: Suit, r: Rank) -> Card:
    return Card(suit=s, rank=r)


def test_idle_scoring_win_and_no_win():
    card_system = CardSystem()
    cps = CardPlayingSystem(card_system=card_system, trump_suit=None)

    # 闲家为 NORTH 与 SOUTH；庄家阵营为 EAST 与 WEST
    cps.set_idle_positions([PlayerPosition.NORTH, PlayerPosition.SOUTH])

    # 第一墩牌：全为黑桃，遵循同花色跟牌
    north_hand_1 = [_make_card(Suit.SPADES, Rank.FIVE)]
    west_hand_1 = [_make_card(Suit.SPADES, Rank.NINE)]
    south_hand_1 = [_make_card(Suit.SPADES, Rank.KING)]  # 最大，SOUTH 应赢墩
    east_hand_1 = [_make_card(Suit.SPADES, Rank.TEN)]

    # 依次出牌（逆时针：North -> West -> South -> East）
    assert cps.play_card(PlayerPosition.NORTH, [north_hand_1[0]], north_hand_1).success
    assert cps.play_card(PlayerPosition.WEST, [west_hand_1[0]], west_hand_1).success
    res3 = cps.play_card(PlayerPosition.SOUTH, [south_hand_1[0]], south_hand_1)
    assert res3.success
    res4 = cps.play_card(PlayerPosition.EAST, [east_hand_1[0]], east_hand_1)
    assert res4.success
    assert res4.winner == PlayerPosition.SOUTH

    # 墩内分牌：5(5分)+10(10分)+K(10分) = 25；赢家 SOUTH 属于闲家，应累计
    assert cps.get_idle_score() == 25
    print("[用例1] 赢家:", res4.winner.value, "闲家累计分:", cps.get_idle_score())

    # 第二墩：应由上一墩赢家 SOUTH 领出，逆时针顺序应为：SOUTH -> EAST -> NORTH -> WEST
    north_hand_2 = [_make_card(Suit.HEARTS, Rank.FIVE)]
    west_hand_2 = [_make_card(Suit.HEARTS, Rank.ACE)]  # 最大，WEST 赢墩
    south_hand_2 = [_make_card(Suit.HEARTS, Rank.TEN)]
    east_hand_2 = [_make_card(Suit.HEARTS, Rank.KING)]

    # 正确由 SOUTH 领出（上一墩赢家），随后应为 EAST -> NORTH -> WEST
    assert cps.play_card(PlayerPosition.SOUTH, [south_hand_2[0]], south_hand_2).success
    assert cps.play_card(PlayerPosition.EAST, [east_hand_2[0]], east_hand_2).success
    assert cps.play_card(PlayerPosition.NORTH, [north_hand_2[0]], north_hand_2).success
    res8 = cps.play_card(PlayerPosition.WEST, [west_hand_2[0]], west_hand_2)
    assert res8.success
    assert res8.winner == PlayerPosition.WEST

    # 第二墩包含：5(5分)+10(10分)+K(10分) = 25 分，但赢家 WEST 非闲家，闲家分仍为 25
    assert cps.get_idle_score() == 25
    print("[用例2] 赢家:", res8.winner.value, "闲家累计分:", cps.get_idle_score())


def test_idle_scoring_idle_wins_no_points():
    card_system = CardSystem()
    cps = CardPlayingSystem(card_system=card_system, trump_suit=None)
    cps.set_idle_positions([PlayerPosition.NORTH, PlayerPosition.SOUTH])

    # 无分牌的一墩，闲家 SOUTH 赢但不应增加分数
    n = [_make_card(Suit.CLUBS, Rank.SEVEN)]
    w = [_make_card(Suit.CLUBS, Rank.SIX)]
    s = [_make_card(Suit.CLUBS, Rank.ACE)]  # 赢墩
    e = [_make_card(Suit.CLUBS, Rank.EIGHT)]

    assert cps.play_card(PlayerPosition.NORTH, [n[0]], n).success
    assert cps.play_card(PlayerPosition.WEST, [w[0]], w).success
    assert cps.play_card(PlayerPosition.SOUTH, [s[0]], s).success
    res = cps.play_card(PlayerPosition.EAST, [e[0]], e)
    assert res.success and res.winner == PlayerPosition.SOUTH
    assert cps.get_idle_score() == 0
    print("[用例3] 赢家:", res.winner.value, "闲家累计分:", cps.get_idle_score())


def test_idle_scoring_trump_eat_non_idle_wins():
    card_system = CardSystem()
    # 设定红桃为主
    cps = CardPlayingSystem(card_system=card_system, trump_suit=Suit.HEARTS)
    cps.set_idle_positions([PlayerPosition.NORTH, PlayerPosition.SOUTH])

    # 领出方黑桃，WEST 全主将吃并赢墩（非闲家），墩内有分牌但不计入闲家
    n = [_make_card(Suit.SPADES, Rank.FIVE)]
    w = [_make_card(Suit.HEARTS, Rank.ACE)]  # 全主且最大
    s = [_make_card(Suit.SPADES, Rank.TEN)]
    e = [_make_card(Suit.HEARTS, Rank.KING)]  # 主牌且有分

    assert cps.play_card(PlayerPosition.NORTH, [n[0]], n).success
    assert cps.play_card(PlayerPosition.WEST, [w[0]], w).success
    assert cps.play_card(PlayerPosition.SOUTH, [s[0]], s).success
    res = cps.play_card(PlayerPosition.EAST, [e[0]], e)
    assert res.success
    # 将吃比较：WEST 与 EAST 都为全主且主最大为 A 与 K，WEST 在先但 EAST 不大于 WEST，因此 WEST 赢
    assert res.winner == PlayerPosition.WEST
    # 墩内分：黑桃5(5分)+黑桃10(10分)+红桃K(10分) = 25，但赢家 WEST 非闲家
    assert cps.get_idle_score() == 0
    print("[用例4] 赢家:", res.winner.value, "闲家累计分:", cps.get_idle_score())



if __name__ == "__main__":
    cases = [
        ("test_idle_scoring_win_and_no_win", test_idle_scoring_win_and_no_win),
        ("test_idle_scoring_idle_wins_no_points", test_idle_scoring_idle_wins_no_points),
        ("test_idle_scoring_trump_eat_non_idle_wins", test_idle_scoring_trump_eat_non_idle_wins),
    ]
    print("==== 开始运行闲家计分测试（脚本直跑）====")
    for name, fn in cases:
        try:
            fn()
            print(f"[{name}] PASS")
        except AssertionError as e:
            print(f"[{name}] FAIL: {e}")
    print("==== 运行完成 ====\n")

