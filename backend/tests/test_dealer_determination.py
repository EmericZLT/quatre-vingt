"""
测试：庄家确定规则
目标：
- 第一局：庄家是定主者
- 第二局及之后：根据闲家得分确定下一局庄家
  - 闲家得分<80分：庄家变为对家（North<->South, East<->West）
  - 闲家得分>=80分：庄家变为下家（North->West->South->East->North）
- 后续局发牌从庄家开始
"""
import os
import sys

# 允许脚本直跑
CURRENT_DIR = os.path.dirname(__file__)
BACKEND_DIR = os.path.abspath(os.path.join(CURRENT_DIR, ".."))
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from app.models.game import GameRoom, Player, PlayerPosition
from app.game.game_state import GameState


def _make_room() -> GameRoom:
    room = GameRoom(id="r1", name="t1")
    room.players = [
        Player(id="pN", name="N", position=PlayerPosition.NORTH, is_ready=True),
        Player(id="pW", name="W", position=PlayerPosition.WEST, is_ready=True),
        Player(id="pS", name="S", position=PlayerPosition.SOUTH, is_ready=True),
        Player(id="pE", name="E", position=PlayerPosition.EAST, is_ready=True),
    ]
    return room


def test_first_round_dealer():
    """测试第一局：庄家是定主者，发牌从随机玩家开始"""
    room = _make_room()
    gs = GameState(room)
    
    assert gs.is_first_round == True
    print("[测试1] 第一局初始状态，is_first_round = True")
    
    # 开始游戏并完成发牌和定主
    ok = gs.start_game()
    assert ok
    
    # 验证第一局发牌顺序已设置（从随机玩家开始）
    assert gs.next_deal_turn_index == 0
    assert len(gs.dealing_order) == 4
    first_dealer_pos = gs.dealing_order[0]
    print(f"[测试1] 第一局发牌从随机玩家开始: {first_dealer_pos.value}")
    
    # 模拟完成发牌
    while gs.game_phase == "dealing":
        gs.deal_tick()
    
    # 模拟定主（找到任意一名玩家的级牌用于定主）
    from app.models.game import Card, Suit, Rank
    
    level_rank = gs.bidding_system._get_level_rank()
    bid_player = None
    level_card = None
    
    # 找到任意一名玩家的级牌用于定主
    for player in gs.room.players:
        for card in player.cards:
            if not card.is_joker and card.rank == level_rank:
                bid_player = player
                level_card = card
                break
        if bid_player:
            break
    
    if level_card and bid_player:
        gs.make_bid(bid_player.id, [level_card])
        gs.finish_bidding()
        
        # 验证第一局庄家是定主者
        assert gs.dealer_position == bid_player.position
        print(f"[测试1] 第一局定主者: {bid_player.id}, 庄家位置: {gs.dealer_position.value} ✓")
    else:
        print("[测试1] 未找到级牌，跳过定主测试")


def test_next_dealer_under_80():
    """测试闲家得分<80分：庄家变为对家"""
    room = _make_room()
    gs = GameState(room)
    
    # 模拟第一局已结束
    gs.is_first_round = False
    
    # 测试North为庄家时，闲家得分<80分，下一局庄家应为South
    gs.dealer_position = PlayerPosition.NORTH
    next_dealer = gs.calculate_next_dealer(idle_score=75)
    assert next_dealer == PlayerPosition.SOUTH
    print(f"[测试2.1] 当前庄家: NORTH, 闲家得分: 75, 下一局庄家: {next_dealer.value} ✓")
    
    # 测试South为庄家时，闲家得分<80分，下一局庄家应为North
    gs.dealer_position = PlayerPosition.SOUTH
    next_dealer = gs.calculate_next_dealer(idle_score=50)
    assert next_dealer == PlayerPosition.NORTH
    print(f"[测试2.2] 当前庄家: SOUTH, 闲家得分: 50, 下一局庄家: {next_dealer.value} ✓")
    
    # 测试East为庄家时，闲家得分<80分，下一局庄家应为West
    gs.dealer_position = PlayerPosition.EAST
    next_dealer = gs.calculate_next_dealer(idle_score=60)
    assert next_dealer == PlayerPosition.WEST
    print(f"[测试2.3] 当前庄家: EAST, 闲家得分: 60, 下一局庄家: {next_dealer.value} ✓")
    
    # 测试West为庄家时，闲家得分<80分，下一局庄家应为East
    gs.dealer_position = PlayerPosition.WEST
    next_dealer = gs.calculate_next_dealer(idle_score=79)
    assert next_dealer == PlayerPosition.EAST
    print(f"[测试2.4] 当前庄家: WEST, 闲家得分: 79, 下一局庄家: {next_dealer.value} ✓")


def test_next_dealer_over_80():
    """测试闲家得分>=80分：庄家变为下家"""
    room = _make_room()
    gs = GameState(room)
    
    # 模拟第一局已结束
    gs.is_first_round = False
    
    # 测试North为庄家时，闲家得分>=80分，下一局庄家应为West
    gs.dealer_position = PlayerPosition.NORTH
    next_dealer = gs.calculate_next_dealer(idle_score=80)
    assert next_dealer == PlayerPosition.WEST
    print(f"[测试3.1] 当前庄家: NORTH, 闲家得分: 80, 下一局庄家: {next_dealer.value} ✓")
    
    # 测试West为庄家时，闲家得分>=80分，下一局庄家应为South
    gs.dealer_position = PlayerPosition.WEST
    next_dealer = gs.calculate_next_dealer(idle_score=100)
    assert next_dealer == PlayerPosition.SOUTH
    print(f"[测试3.2] 当前庄家: WEST, 闲家得分: 100, 下一局庄家: {next_dealer.value} ✓")
    
    # 测试South为庄家时，闲家得分>=80分，下一局庄家应为East
    gs.dealer_position = PlayerPosition.SOUTH
    next_dealer = gs.calculate_next_dealer(idle_score=120)
    assert next_dealer == PlayerPosition.EAST
    print(f"[测试3.3] 当前庄家: SOUTH, 闲家得分: 120, 下一局庄家: {next_dealer.value} ✓")
    
    # 测试East为庄家时，闲家得分>=80分，下一局庄家应为North
    gs.dealer_position = PlayerPosition.EAST
    next_dealer = gs.calculate_next_dealer(idle_score=200)
    assert next_dealer == PlayerPosition.NORTH
    print(f"[测试3.4] 当前庄家: EAST, 闲家得分: 200, 下一局庄家: {next_dealer.value} ✓")


def test_end_round():
    """测试结束一局游戏，计算下一局庄家"""
    room = _make_room()
    gs = GameState(room)
    
    # 模拟第一局已开始并设置庄家
    gs.is_first_round = False
    gs.dealer_position = PlayerPosition.NORTH
    gs.game_phase = "playing"
    
    # 测试结束一局，闲家得分<80分
    ok = gs.end_round(idle_score=75)
    assert ok
    assert gs.dealer_position == PlayerPosition.SOUTH
    assert gs.is_first_round == False
    assert gs.game_phase == "waiting"
    print(f"[测试4.1] 结束一局，闲家得分: 75, 下一局庄家: {gs.dealer_position.value} ✓")
    
    # 测试结束一局，闲家得分>=80分
    gs.dealer_position = PlayerPosition.NORTH
    gs.game_phase = "playing"
    ok = gs.end_round(idle_score=80)
    assert ok
    assert gs.dealer_position == PlayerPosition.WEST
    assert gs.is_first_round == False
    assert gs.game_phase == "waiting"
    print(f"[测试4.2] 结束一局，闲家得分: 80, 下一局庄家: {gs.dealer_position.value} ✓")


def test_dealing_order_from_dealer():
    """测试后续局发牌从庄家开始"""
    room = _make_room()
    gs = GameState(room)
    
    # 模拟第一局已结束，当前庄家是West
    gs.is_first_round = False
    gs.dealer_position = PlayerPosition.WEST
    
    # 设置发牌顺序
    gs._set_dealing_order_from_dealer()
    
    # 验证发牌顺序从West开始
    assert gs.dealing_order[0] == PlayerPosition.WEST
    assert gs.dealing_order[1] == PlayerPosition.SOUTH
    assert gs.dealing_order[2] == PlayerPosition.EAST
    assert gs.dealing_order[3] == PlayerPosition.NORTH
    assert gs.next_deal_turn_index == 0
    print(f"[测试5] 庄家: WEST, 发牌顺序: {[p.value for p in gs.dealing_order]} ✓")
    
    # 测试North为庄家
    gs.dealer_position = PlayerPosition.NORTH
    gs._set_dealing_order_from_dealer()
    assert gs.dealing_order[0] == PlayerPosition.NORTH
    assert gs.next_deal_turn_index == 0
    print(f"[测试5.1] 庄家: NORTH, 发牌顺序: {[p.value for p in gs.dealing_order]} ✓")
    
    # 测试South为庄家
    gs.dealer_position = PlayerPosition.SOUTH
    gs._set_dealing_order_from_dealer()
    assert gs.dealing_order[0] == PlayerPosition.SOUTH
    assert gs.next_deal_turn_index == 0
    print(f"[测试5.2] 庄家: SOUTH, 发牌顺序: {[p.value for p in gs.dealing_order]} ✓")
    
    # 测试East为庄家
    gs.dealer_position = PlayerPosition.EAST
    gs._set_dealing_order_from_dealer()
    assert gs.dealing_order[0] == PlayerPosition.EAST
    assert gs.next_deal_turn_index == 0
    print(f"[测试5.3] 庄家: EAST, 发牌顺序: {[p.value for p in gs.dealing_order]} ✓")


def test_multiple_rounds():
    """测试多局游戏的庄家变化"""
    room = _make_room()
    gs = GameState(room)
    
    # 第一局：假设North定主
    assert gs.is_first_round == True
    print("\n[多局测试] 第一局：假设North定主")
    
    # 模拟第一局结束，当前庄家NORTH，闲家得分<80分
    gs.is_first_round = False
    gs.dealer_position = PlayerPosition.NORTH
    gs.game_phase = "playing"  # 必须设置为playing才能调用end_round
    gs.end_round(idle_score=60)
    # 得分<80，庄家变为对家：NORTH -> SOUTH
    assert gs.dealer_position == PlayerPosition.SOUTH
    print(f"[多局测试] 第一局结束，当前庄家: NORTH, 闲家得分: 60, 下一局庄家: {gs.dealer_position.value}")
    
    # 第二局结束，当前庄家SOUTH（已由上一局自动更新），闲家得分>=80分
    gs.game_phase = "playing"
    gs.end_round(idle_score=100)
    # 得分>=80，庄家变为下家：SOUTH -> EAST
    assert gs.dealer_position == PlayerPosition.EAST
    print(f"[多局测试] 第二局结束，当前庄家: SOUTH, 闲家得分: 100, 下一局庄家: {gs.dealer_position.value}")
    
    # 第三局结束，当前庄家EAST，闲家得分<80分
    gs.game_phase = "playing"
    gs.end_round(idle_score=50)
    # 得分<80，庄家变为对家：EAST -> WEST
    assert gs.dealer_position == PlayerPosition.WEST
    print(f"[多局测试] 第三局结束，当前庄家: EAST, 闲家得分: 50, 下一局庄家: {gs.dealer_position.value}")
    
    # 第四局结束，当前庄家WEST，闲家得分>=80分
    gs.game_phase = "playing"
    gs.end_round(idle_score=80)
    # 得分>=80，庄家变为下家：WEST -> SOUTH
    assert gs.dealer_position == PlayerPosition.SOUTH
    print(f"[多局测试] 第四局结束，当前庄家: WEST, 闲家得分: 80, 下一局庄家: {gs.dealer_position.value} ✓")


if __name__ == "__main__":
    print("==== 开始运行庄家确定规则测试 ====")
    
    test_cases = [
        ("test_first_round_dealer", test_first_round_dealer),
        ("test_next_dealer_under_80", test_next_dealer_under_80),
        ("test_next_dealer_over_80", test_next_dealer_over_80),
        ("test_end_round", test_end_round),
        ("test_dealing_order_from_dealer", test_dealing_order_from_dealer),
        ("test_multiple_rounds", test_multiple_rounds),
    ]
    
    for name, test_func in test_cases:
        try:
            test_func()
            print(f"[{name}] PASS\n")
        except AssertionError as e:
            print(f"[{name}] FAIL: {e}\n")
    
    print("==== 所有测试完成 ====")

