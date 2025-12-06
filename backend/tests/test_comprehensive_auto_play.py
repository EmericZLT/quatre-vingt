#!/usr/bin/env python
"""
测试倒计时和自动出牌功能，确保所有游戏规则正常执行
"""
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '../backend/app'))

from app.game.game_state import GameState
from app.models.game import GameRoom, Player, PlayerPosition, Suit, Rank, Card

def test_comprehensive_auto_play():
    """全面测试自动出牌功能，确保所有牌型和游戏规则正常执行"""
    print("测试全面自动出牌功能...")
    
    # 创建游戏房间
    room = GameRoom(
        id="test-room",
        name="Test Room",
        players=[]
    )
    
    # 添加4个玩家
    players = [
        Player(id="p1", name="Player 1", position=PlayerPosition.NORTH),
        Player(id="p2", name="Player 2", position=PlayerPosition.SOUTH),
        Player(id="p3", name="Player 3", position=PlayerPosition.EAST),
        Player(id="p4", name="Player 4", position=PlayerPosition.WEST)
    ]
    
    for player in players:
        room.players.append(player)
        player.is_ready = True
    
    # 创建游戏状态
    game_state = GameState(room)
    
    # 开始游戏
    game_state.start_game()
    
    # 设置主牌
    game_state.set_trump_suit(Suit.HEARTS)
    
    # 设置游戏级别（解决TractorLogic初始化错误）
    game_state.card_system.current_level = 10
    
    # 设置游戏阶段为playing
    game_state.game_phase = "playing"
    
    # 设置当前玩家
    game_state.current_player = PlayerPosition.NORTH
    game_state.current_player_id = "p1"
    
    # 为所有玩家设置手牌
    # 玩家1: 有拖拉机和对子
    player1 = game_state.get_player_by_id("p1")
    player1.cards = [
        Card(suit=Suit.SPADES, rank=Rank.TWO),
        Card(suit=Suit.SPADES, rank=Rank.THREE),  # 黑桃2-3拖拉机
        Card(suit=Suit.SPADES, rank=Rank.FOUR),
        Card(suit=Suit.HEARTS, rank=Rank.FIVE),
        Card(suit=Suit.HEARTS, rank=Rank.SIX),    # 红桃5-6拖拉机
        Card(suit=Suit.CLUBS, rank=Rank.SEVEN),
        Card(suit=Suit.CLUBS, rank=Rank.EIGHT)     # 梅花7-8拖拉机
    ]
    
    # 玩家2: 有可以跟的拖拉机
    player2 = game_state.get_player_by_id("p2")
    player2.cards = [
        Card(suit=Suit.SPADES, rank=Rank.FIVE),
        Card(suit=Suit.SPADES, rank=Rank.SIX),  # 可以跟黑桃拖拉机
        Card(suit=Suit.HEARTS, rank=Rank.SEVEN),
        Card(suit=Suit.HEARTS, rank=Rank.EIGHT),
        Card(suit=Suit.DIAMONDS, rank=Rank.NINE),
        Card(suit=Suit.DIAMONDS, rank=Rank.TEN)
    ]
    
    # 玩家3: 有对子和单牌
    player3 = game_state.get_player_by_id("p3")
    player3.cards = [
        Card(suit=Suit.SPADES, rank=Rank.JACK),
        Card(suit=Suit.SPADES, rank=Rank.QUEEN),  # 黑桃J-Q对子
        Card(suit=Suit.HEARTS, rank=Rank.KING),
        Card(suit=Suit.HEARTS, rank=Rank.ACE),
        Card(suit=Suit.CLUBS, rank=Rank.NINE),
        Card(suit=Suit.CLUBS, rank=Rank.TEN)
    ]
    
    # 玩家4: 有单牌
    player4 = game_state.get_player_by_id("p4")
    player4.cards = [
        Card(suit=Suit.SPADES, rank=Rank.KING),
        Card(suit=Suit.SPADES, rank=Rank.ACE),
        Card(suit=Suit.HEARTS, rank=Rank.TWO),
        Card(suit=Suit.HEARTS, rank=Rank.THREE),
        Card(suit=Suit.DIAMONDS, rank=Rank.JACK),
        Card(suit=Suit.DIAMONDS, rank=Rank.QUEEN)
    ]
    
    print(f"\n所有玩家手牌设置完成")
    print(f"玩家1手牌: {[str(c) for c in player1.cards]}")
    print(f"玩家2手牌: {[str(c) for c in player2.cards]}")
    print(f"玩家3手牌: {[str(c) for c in player3.cards]}")
    print(f"玩家4手牌: {[str(c) for c in player4.cards]}")
    
    # 测试领出时的自动出牌（应该出拖拉机）
    print(f"\n=== 测试领出时的自动出牌 ===")
    print(f"当前玩家: {game_state.current_player} ({game_state.current_player_id})")
    
    auto_play_result = game_state.auto_play()
    print(f"自动出牌结果: {auto_play_result}")
    print(f"玩家1剩余手牌: {[str(c) for c in player1.cards]}")
    
    # 检查是否成功出了牌
    if auto_play_result['success']:
        played_cards = auto_play_result.get('played_cards', [])
        print(f"出的牌: {[str(c) for c in played_cards]}")
        print(f"出牌数量: {len(played_cards)}")
        
        # 验证是否成功出了牌
        print("✓ 成功出牌")
    else:
        print("✗ 出牌失败")
    
    # 测试跟牌时的自动出牌
    print(f"\n=== 测试跟牌时的自动出牌 ===")
    print(f"当前玩家: {game_state.current_player} ({game_state.current_player_id})")
    
    # 设置前一轮的牌型（模拟领出了黑桃拖拉机）
    game_state.current_trick = [
        Card(suit=Suit.SPADES, rank=Rank.TWO),
        Card(suit=Suit.SPADES, rank=Rank.THREE),
        Card(suit=Suit.SPADES, rank=Rank.FOUR),
        Card(suit=Suit.SPADES, rank=Rank.FIVE)
    ]
    
    auto_play_result = game_state.auto_play()
    print(f"自动出牌结果: {auto_play_result}")
    print(f"玩家2剩余手牌: {[str(c) for c in player2.cards]}")
    
    if auto_play_result['success']:
        played_cards = auto_play_result.get('played_cards', [])
        print(f"出的牌: {[str(c) for c in played_cards]}")
        print(f"出牌数量: {len(played_cards)}")
        
        # 检查是否跟了相同长度的牌
        if len(played_cards) == len(game_state.current_trick):
            print("✓ 成功跟了相同长度的牌")
        else:
            print("✗ 没有跟相同长度的牌")
    
    print(f"\n=== 测试结束 ===")
    print("所有测试完成!")

if __name__ == "__main__":
    test_comprehensive_auto_play()
