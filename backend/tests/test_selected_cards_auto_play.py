#!/usr/bin/env python3
"""
测试使用选中卡牌自动出牌功能
简化测试场景，只测试选中卡牌的处理逻辑
"""

import sys
import os

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.game.game_state import GameState
from app.models.game import GameRoom, Player, PlayerPosition, Card, Suit, Rank

def create_new_game_state():
    """创建新的游戏状态，用于每个测试场景"""
    # 创建测试用的游戏房间
    room = GameRoom(id="test_room", name="测试房间")
    
    # 创建4个玩家
    player1 = Player(id="p1", name="Player1", position=PlayerPosition.NORTH)
    player2 = Player(id="p2", name="Player2", position=PlayerPosition.EAST)
    player3 = Player(id="p3", name="Player3", position=PlayerPosition.SOUTH)
    player4 = Player(id="p4", name="Player4", position=PlayerPosition.WEST)
    
    # 将玩家添加到房间
    room.players = [player1, player2, player3, player4]
    
    # 创建游戏状态
    game = GameState(room)
    
    # 设置游戏参数
    game.game_phase = "playing"
    game.trump_suit = Suit.SPADES  # 主牌花色：黑桃
    game.current_level = 1
    game.east_west_level = 1
    game.north_south_level = 1
    
    # 设置当前玩家
    game.current_player = PlayerPosition.NORTH
    
    # 初始化出牌系统
    game._init_card_playing_system()
    
    # 给当前玩家发牌
    player1.cards = [
        Card(suit=Suit.HEARTS, rank=Rank.THREE),
        Card(suit=Suit.HEARTS, rank=Rank.FOUR),
        Card(suit=Suit.SPADES, rank=Rank.FIVE),  # 主牌
        Card(suit=Suit.CLUBS, rank=Rank.SIX),
        Card(suit=Suit.DIAMONDS, rank=Rank.SEVEN)
    ]
    
    return game, player1

# 测试场景1：领出时选中符合规则的卡牌（单张）
print("=== 测试场景1: 领出时选中符合规则的卡牌（单张） ===")
game, player1 = create_new_game_state()

print("玩家1手牌:", [str(card) for card in player1.cards])

# 直接从玩家手牌中选择卡牌，确保是同一个对象实例
selected_cards_valid = [player1.cards[0]]  # 选择第一张牌
print("选中的卡牌:", [str(card) for card in selected_cards_valid])

game.selected_cards = selected_cards_valid

auto_play_result = game.auto_play()
print("自动出牌结果:", auto_play_result)
print("玩家1剩余手牌:", [str(card) for card in player1.cards])

# 验证结果
if auto_play_result["success"]:
    played_cards = auto_play_result["played_cards"]
    if all(card in played_cards for card in selected_cards_valid):
        print("✓ 测试通过：领出时成功使用了选中的符合规则的卡牌")
    else:
        print("✗ 测试失败：领出时没有使用选中的卡牌")
else:
    print("✗ 测试失败：领出时自动出牌失败")

# 测试场景2：领出时选中了不符合规则的卡牌（不同花色多张）
print("\n=== 测试场景2: 领出时选中不符合规则的卡牌（不同花色多张） ===")
game, player1 = create_new_game_state()

print("玩家1手牌:", [str(card) for card in player1.cards])

# 直接从玩家手牌中选择卡牌，确保是同一个对象实例
selected_cards_invalid = [player1.cards[0], player1.cards[3]]  # 选择不同花色的卡牌
print("选中的卡牌:", [str(card) for card in selected_cards_invalid])

game.selected_cards = selected_cards_invalid

auto_play_result = game.auto_play()
print("自动出牌结果:", auto_play_result)

# 验证结果
if auto_play_result["success"]:
    print("✓ 测试通过：领出时自动处理了不符合规则的选中卡牌")
else:
    print("✗ 测试失败：领出时自动出牌失败")

print("\n所有测试场景完成!")