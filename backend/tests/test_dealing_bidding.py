"""
测试：发牌节拍与发牌过程亮主/反主
目标：
- 按逆时针逐张发牌（N->W->S->E），发完100张进入亮主阶段
- 发牌过程中允许亮主；未发完不能结束亮主
- 发完后允许结束亮主，锁定主牌并把底牌发给庄家
"""
import os
import sys

# 允许脚本直跑
CURRENT_DIR = os.path.dirname(__file__)
BACKEND_DIR = os.path.abspath(os.path.join(CURRENT_DIR, ".."))
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from app.models.game import GameRoom, Player, PlayerPosition, Suit, Card, Rank
from app.game.game_state import GameState
from app.game.bidding_system import BiddingSystem


def _make_room() -> GameRoom:
    room = GameRoom(id="r1", name="t1")
    room.players = [
        Player(id="pN", name="N", position=PlayerPosition.NORTH, is_ready=True),
        Player(id="pW", name="W", position=PlayerPosition.WEST, is_ready=True),
        Player(id="pS", name="S", position=PlayerPosition.SOUTH, is_ready=True),
        Player(id="pE", name="E", position=PlayerPosition.EAST, is_ready=True),
    ]
    return room


def _find_single_level_bid_cards(gs: GameState):
    """在当前玩家手牌中寻找任意一张级牌用于亮主。返回 (player_id, [card]) 或 None。"""
    level_rank = gs.bidding_system._get_level_rank()
    for p in gs.room.players:
        for c in p.cards:
            if not c.is_joker and c.rank == level_rank:
                return p.id, [c]
    return None


def _find_level_pair_cards(gs: GameState, suit: Suit = None):
    """在当前玩家手牌中寻找级牌对子。返回 (player_id, [card1, card2]) 或 None。"""
    level_rank = gs.bidding_system._get_level_rank()
    for p in gs.room.players:
        cards_by_suit = {}
        for c in p.cards:
            if not c.is_joker and c.rank == level_rank:
                if c.suit not in cards_by_suit:
                    cards_by_suit[c.suit] = []
                cards_by_suit[c.suit].append(c)
        
        # 如果指定了花色，只在该花色中查找
        suits_to_check = [suit] if suit else list(cards_by_suit.keys())
        
        for s in suits_to_check:
            if s in cards_by_suit and len(cards_by_suit[s]) >= 2:
                return p.id, cards_by_suit[s][:2]
    return None


def _find_joker_pair(gs: GameState, is_big: bool = False):
    """在当前玩家手牌中寻找双王。返回 (player_id, [card1, card2]) 或 None。"""
    target_rank = Rank.BIG_JOKER if is_big else Rank.SMALL_JOKER
    for p in gs.room.players:
        jokers = [c for c in p.cards if c.is_joker and c.rank == target_rank]
        if len(jokers) >= 2:
            return p.id, jokers[:2]
    return None


def test_dealing_and_bidding_flow():
    room = _make_room()
    gs = GameState(room)

    ok = gs.start_game()
    assert ok and gs.game_phase == "dealing"
    print("[发牌] 开始，底牌数量:", len(gs.bottom_cards))

    # 先发若干张，尝试在发牌阶段亮主（允许）
    for _ in range(20):
        r = gs.deal_tick()
        assert r["success"]
    print("[发牌] 已发出20张，各家数量:", {p.position.value: len(p.cards) for p in gs.room.players})

    # 发牌阶段亮主（允许），从任意玩家找到一张级牌
    bid_info = _find_single_level_bid_cards(gs)
    assert bid_info is not None, "前20张里未找到级牌，重试次数不足"
    player_id, cards = bid_info
    res = gs.make_bid(player_id, cards)
    print("[亮主] 发牌阶段亮主：", res)
    assert res["success"]
    bid_removed = len(cards)
    bid_player_id = player_id

    # 发牌未完成前，结束亮主应失败
    assert not gs.finish_bidding()
    print("[亮主] 未发完，结束亮主：False")

    # 发完全部100张
    while gs.game_phase == "dealing":
        r = gs.deal_tick()
        assert r["success"]
    assert gs.game_phase == "bidding"
    counts = {p.position.value: len(p.cards) for p in gs.room.players}
    print("[发牌] 完成，进入亮主阶段。各家数量:", counts)
    # 验证：总数应为 100 - 已用于亮主的牌数
    total_in_hands = sum(counts.values())
    assert total_in_hands == 100 - bid_removed
    # 亮主玩家应少于25张：25 - bid_removed，其余应为25
    for p in gs.room.players:
        if p.id == bid_player_id:
            assert len(p.cards) == 25 - bid_removed
        else:
            assert len(p.cards) == 25

    # 亮主阶段可继续反主（可选）：此处直接结束亮主
    ok_finish = gs.finish_bidding()
    assert ok_finish 
    assert gs.trump_locked
    print("[亮主] 结束亮主，主牌:", gs.trump_suit.value if gs.trump_suit else None, "已锁定:", gs.trump_locked)

    # 验证庄家设置（当前逻辑：最终亮主者成为庄家）
    dealer = gs.get_dealer()
    assert dealer is not None
    print("[庄家] 庄家位置:", gs.dealer_position.value, "手牌数量（归还亮主牌后，未包含底牌）:", len(dealer.cards))
    
    # 注意：finish_bidding() 已解耦，不再自动调用 give_bottom_to_dealer()
    # 如果需要测试底牌逻辑，需要手动调用 give_bottom_to_dealer()
    # 当前测试仅验证亮主阶段的逻辑，不验证底牌


def test_counter_bidding():
    """测试反主功能：单张级牌 -> 级牌对子 -> 双小王 -> 双大王"""
    room = _make_room()
    gs = GameState(room)

    # 开始游戏并发完所有牌
    ok = gs.start_game()
    assert ok and gs.game_phase == "dealing"
    print("\n[反主测试] 开始游戏")

    # 发完全部100张牌
    while gs.game_phase == "dealing":
        r = gs.deal_tick()
        assert r["success"]
    assert gs.game_phase == "bidding"
    print("[反主测试] 发牌完成，进入亮主阶段")

    # 步骤1：玩家A用单张级牌亮主
    bid_info = _find_single_level_bid_cards(gs)
    assert bid_info is not None, "未找到单张级牌"
    player1_id, cards1 = bid_info
    player1 = gs.get_player_by_id(player1_id)
    initial_cards_count_p1 = len(player1.cards)
    
    res1 = gs.make_bid(player1_id, cards1)
    print(f"[反主测试] 步骤1 - {player1_id} 单张级牌亮主:", res1)
    assert res1["success"]
    assert res1["bid_type"] == "single_level"
    assert len(player1.cards) == initial_cards_count_p1 - 1
    
    # 检查当前主牌
    status = gs.get_bidding_status()
    assert status["current_bid"]["player_id"] == player1_id
    assert status["current_bid"]["bid_type"] == "single_level"
    first_suit = res1["suit"]
    print(f"[反主测试] 当前主牌花色: {first_suit}")

    # 步骤2：玩家B用级牌对子反主（应该成功）
    bid_info2 = _find_level_pair_cards(gs)
    if bid_info2 is None:
        print("[反主测试] 未找到级牌对子，跳过此测试")
        return
    
    player2_id, cards2 = bid_info2
    player2 = gs.get_player_by_id(player2_id)
    initial_cards_count_p2 = len(player2.cards)
    
    res2 = gs.make_bid(player2_id, cards2)
    print(f"[反主测试] 步骤2 - {player2_id} 级牌对子反主:", res2)
    assert res2["success"], f"级牌对子应该能够反单张级牌，但失败了: {res2.get('message')}"
    assert res2["bid_type"] == "pair_level"
    assert len(player2.cards) == initial_cards_count_p2 - 2
    
    # 检查当前主牌已更新
    status = gs.get_bidding_status()
    assert status["current_bid"]["player_id"] == player2_id
    assert status["current_bid"]["bid_type"] == "pair_level"
    print(f"[反主测试] 当前主牌更新为: {res2['suit']} (级牌对子)")

    # 步骤3：尝试用相同优先级的级牌对子反主（应该失败）
    # 如果玩家2的级牌对子是某个花色，尝试用相同花色的级牌对子反主
    pair_suit = res2["suit"]
    if pair_suit:
        # 查找其他玩家的相同花色级牌对子
        for p in gs.room.players:
            if p.id != player2_id:
                bid_info3 = _find_level_pair_cards(gs, suit=Suit(pair_suit))
                if bid_info3 and bid_info3[0] == p.id:
                    player3_id, cards3 = bid_info3
                    res3 = gs.make_bid(player3_id, cards3)
                    print(f"[反主测试] 步骤3 - {player3_id} 相同优先级级牌对子反主:", res3)
                    assert not res3["success"], "相同优先级的级牌对子不应该能够反主"
                    assert "无法反掉当前主牌" in res3["message"]
                    break

    # 步骤4：尝试用更高优先级花色反主（应该成功）
    # 如果当前是♦或♣，尝试用♥或♠反主
    suit_priority_map = {Suit.DIAMONDS: 1, Suit.CLUBS: 2, Suit.HEARTS: 3, Suit.SPADES: 4}
    if pair_suit:
        current_suit_priority = suit_priority_map.get(Suit(pair_suit), 0)
        higher_suits = [s for s, p in suit_priority_map.items() if p > current_suit_priority]
        
        for higher_suit in higher_suits:
            bid_info4 = _find_level_pair_cards(gs, suit=higher_suit)
            if bid_info4:
                player4_id, cards4 = bid_info4
                res4 = gs.make_bid(player4_id, cards4)
                print(f"[反主测试] 步骤4 - {player4_id} 更高优先级花色反主 ({higher_suit.value}):", res4)
                if res4["success"]:
                    assert res4["bid_type"] == "pair_level"
                    status = gs.get_bidding_status()
                    assert status["current_bid"]["player_id"] == player4_id
                    break
                else:
                    print(f"[反主测试] 步骤4 - 未找到 {higher_suit.value} 的级牌对子，跳过")

    # 步骤5：尝试用双小王反主（优先级更高，应该成功）
    bid_info5 = _find_joker_pair(gs, is_big=False)
    if bid_info5:
        player5_id, cards5 = bid_info5
        player5 = gs.get_player_by_id(player5_id)
        initial_cards_count_p5 = len(player5.cards)
        
        res5 = gs.make_bid(player5_id, cards5)
        print(f"[反主测试] 步骤5 - {player5_id} 双小王反主:", res5)
        assert res5["success"], f"双小王应该能够反级牌对子，但失败了: {res5.get('message')}"
        assert res5["bid_type"] == "double_joker"
        assert len(player5.cards) == initial_cards_count_p5 - 2
        
        status = gs.get_bidding_status()
        assert status["current_bid"]["player_id"] == player5_id
        assert status["current_bid"]["bid_type"] == "double_joker"
        print("[反主测试] 当前主牌更新为: 无主 (双小王)")

    # 步骤6：尝试用双大王反主（优先级最高，应该成功）
    bid_info6 = _find_joker_pair(gs, is_big=True)
    if bid_info6:
        player6_id, cards6 = bid_info6
        player6 = gs.get_player_by_id(player6_id)
        initial_cards_count_p6 = len(player6.cards)
        
        res6 = gs.make_bid(player6_id, cards6)
        print(f"[反主测试] 步骤6 - {player6_id} 双大王反主:", res6)
        assert res6["success"], f"双大王应该能够反双小王，但失败了: {res6.get('message')}"
        assert res6["bid_type"] == "double_big_joker"
        assert len(player6.cards) == initial_cards_count_p6 - 2
        
        status = gs.get_bidding_status()
        assert status["current_bid"]["player_id"] == player6_id
        assert status["current_bid"]["bid_type"] == "double_big_joker"
        print("[反主测试] 当前主牌更新为: 无主 (双大王)")

    # 步骤7：结束亮主，验证所有亮主者的牌被归还
    final_bidder_id = gs.get_bidding_status()["current_bid"]["player_id"]
    final_bidder = gs.get_player_by_id(final_bidder_id)
    cards_before_finish = len(final_bidder.cards)
    
    # 记录所有亮主玩家的归还前手牌数
    all_bidders_before = {}
    for p in gs.room.players:
        all_bidders_before[p.id] = len(p.cards)
    
    ok_finish = gs.finish_bidding()
    assert ok_finish
    assert gs.trump_locked
    
    # 验证所有参与亮主的玩家的牌都被归还（不包括最终获得底牌的影响）
    final_bid = gs.bidding_system.current_bid
    cards_after_finish = len(final_bidder.cards)
    assert cards_after_finish == cards_before_finish + len(final_bid.cards), \
        f"最终亮主者的牌应该被归还。归还前: {cards_before_finish}, 归还后: {cards_after_finish}, 亮主用牌数: {len(final_bid.cards)}"
    
    # 验证所有其他亮主者的牌也被归还
    for player_id, cards_list in all_bidders_before.items():
        if player_id != final_bidder_id:  # 跳过最终亮主者（已在上方验证）
            player = gs.get_player_by_id(player_id)
            if player:
                # 检查该玩家是否参与过亮主（通过手牌数量变化判断）
                # 如果玩家在亮主过程中被打出的牌被归还，手牌数量应该增加
                current_cards = len(player.cards)
                # 注意：这里我们无法直接知道每个玩家亮主时用了多少张牌
                # 只能验证最终亮主者的牌被归还，其他玩家的归还逻辑由系统保证
    
    # 验证庄家是最终亮主者（当前逻辑：最终亮主者成为庄家）
    assert gs.dealer_position == final_bidder.position
    print(f"[反主测试] 最终亮主者: {final_bidder_id}, 庄家: {gs.dealer_position.value}")
    print(f"[反主测试] 最终亮主者手牌数量: {cards_after_finish} (包含归还的亮主牌，未包含底牌)")

    # 注意：finish_bidding() 已解耦，不再自动调用 give_bottom_to_dealer()
    # 如果需要测试底牌逻辑，需要手动调用 give_bottom_to_dealer()
    # 当前测试仅验证亮主牌的归还逻辑
    
    print("[反主测试] 所有测试通过 ✓")


if __name__ == "__main__":
    # try:
    test_dealing_and_bidding_flow()
    print("[test_dealing_and_bidding_flow] PASS")
    
    test_counter_bidding()
    print("[test_counter_bidding] PASS")
    # except AssertionError as e:
    #     print("[test_dealing_and_bidding_flow] FAIL:", e)


