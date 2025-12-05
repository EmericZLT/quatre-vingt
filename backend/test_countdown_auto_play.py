#!/usr/bin/env python
"""
测试倒计时和自动出牌功能
"""
import sys
import os
import asyncio
import time
sys.path.append(os.path.join(os.path.dirname(__file__), '../backend/app'))

from app.game.game_state import GameState
from app.models.game import GameRoom, Player, PlayerPosition, Suit, Rank, Card

async def test_countdown_and_auto_play():
    """测试倒计时和自动出牌功能"""
    print("测试倒计时和自动出牌功能...")
    
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
    
    # 设置游戏阶段为playing
    game_state.game_phase = "playing"
    
    # 设置当前玩家
    game_state.current_player = PlayerPosition.NORTH
    game_state.current_player_id = "p1"
    
    # 为玩家1设置一些手牌
    player1 = game_state.get_player_by_id("p1")
    player1.cards = [
        Card(suit=Suit.SPADES, rank=Rank.TWO),
        Card(suit=Suit.HEARTS, rank=Rank.THREE),
        Card(suit=Suit.CLUBS, rank=Rank.FOUR)
    ]
    
    # 为玩家2设置一些手牌
    player2 = game_state.get_player_by_id("p2")
    player2.cards = [
        Card(suit=Suit.SPADES, rank=Rank.THREE),
        Card(suit=Suit.HEARTS, rank=Rank.FOUR),
        Card(suit=Suit.DIAMONDS, rank=Rank.FIVE)
    ]
    
    # 检查初始倒计时状态
    print(f"\n初始倒计时状态:")
    print(f"max_play_time: {game_state.max_play_time}")
    print(f"current_countdown: {game_state.current_countdown}")
    print(f"countdown_active: {game_state.countdown_active}")
    print(f"current_player_id: {game_state.current_player_id}")
    
    # 开始倒计时
    print(f"\n开始倒计时...")
    game_state.start_countdown()
    
    # 检查倒计时启动状态
    print(f"countdown_active: {game_state.countdown_active}")
    print(f"current_countdown: {game_state.current_countdown}")
    
    # 直接调用decrease_countdown方法测试倒计时
    game_state.decrease_countdown()
    print(f"1次decrease后 current_countdown: {game_state.current_countdown}")
    
    game_state.decrease_countdown()
    print(f"2次decrease后 current_countdown: {game_state.current_countdown}")
    
    game_state.decrease_countdown()
    print(f"3次decrease后 current_countdown: {game_state.current_countdown}")
    
    # 停止倒计时
    game_state.stop_countdown()
    print(f"\n停止倒计时后:")
    print(f"countdown_active: {game_state.countdown_active}")
    
    # 测试玩家1出牌后倒计时重启功能
    print(f"\n测试玩家1出牌后倒计时重启功能...")
    print(f"出牌前当前玩家: {game_state.current_player}")
    print(f"出牌前当前玩家ID: {game_state.current_player_id}")
    
    # 玩家1出牌
    card_to_play = [Card(suit=Suit.SPADES, rank=Rank.TWO)]
    result = game_state.play_card("p1", card_to_play)
    print(f"玩家1出牌结果: {result}")
    
    # 检查当前玩家是否已更新为玩家2
    print(f"出牌后当前玩家: {game_state.current_player}")
    print(f"出牌后当前玩家ID: {game_state.current_player_id}")
    
    # 为玩家2启动倒计时
    game_state.start_countdown()
    print(f"\n为玩家2启动倒计时后:")
    print(f"countdown_active: {game_state.countdown_active}")
    print(f"current_countdown: {game_state.current_countdown}")
    
    # 直接调用decrease_countdown方法测试倒计时
    game_state.decrease_countdown()
    print(f"1次decrease后 current_countdown: {game_state.current_countdown}")
    
    game_state.decrease_countdown()
    print(f"2次decrease后 current_countdown: {game_state.current_countdown}")
    
    # 测试自动出牌
    print(f"\n测试自动出牌功能...")
    if game_state.current_player:
        current_player = game_state.get_player_by_position(game_state.current_player)
        if current_player:
            print(f"当前玩家: {current_player.name}")
            print(f"当前玩家ID: {current_player.id}")
            print(f"当前玩家手牌数量: {len(current_player.cards)}")
            
            # 调用自动出牌
            auto_played = game_state.auto_play()
            print(f"自动出牌结果: {auto_played}")
            print(f"出牌后手牌数量: {len(current_player.cards)}")
    
    print(f"\n测试完成!")

if __name__ == "__main__":
    asyncio.run(test_countdown_and_auto_play())