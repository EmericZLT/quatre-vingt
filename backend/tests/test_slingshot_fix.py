#!/usr/bin/env python3
"""
测试甩牌修复效果：当玩家尝试甩牌失败时，自动使用强制要求出的牌
"""
import sys
import os

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.game.game_state import GameState
from app.models.game import GameRoom, Player, PlayerPosition, Card, Suit, Rank


def test_slingshot_fix():
    """测试甩牌失败时是否自动使用强制要求的牌"""
    print("=== 测试甩牌修复效果 ===")
    
    # 创建游戏状态
    def create_new_game_state():
        game_state = GameState(room=GameRoom(id="test_room", name="测试房间"))
        game_state.game_phase = "playing"
        game_state.trump_suit = Suit.SPADES  # 主牌花色：黑桃
        game_state.current_level = 1
        game_state.east_west_level = 1
        game_state.north_south_level = 1
        
        # 初始化出牌系统
        game_state._init_card_playing_system()
        
        # 创建玩家
        player1 = Player(id="player1", name="Player1", position=PlayerPosition.NORTH)
        player2 = Player(id="player2", name="Player2", position=PlayerPosition.WEST)
        player3 = Player(id="player3", name="Player3", position=PlayerPosition.SOUTH)
        player4 = Player(id="player4", name="Player4", position=PlayerPosition.EAST)
        
        # 设置玩家手牌
        # player1: 3♥, 6♣, 5♥ (有红桃牌)
        # player2: 4♥ (有比3♥大的红桃牌，使甩牌失败)
        player1.cards = [
            Card(suit=Suit.HEARTS, rank=Rank.THREE),
            Card(suit=Suit.CLUBS, rank=Rank.SIX),
            Card(suit=Suit.HEARTS, rank=Rank.FIVE)
        ]
        player2.cards = [
            Card(suit=Suit.HEARTS, rank=Rank.FOUR),
            Card(suit=Suit.SPADES, rank=Rank.SEVEN),
            Card(suit=Suit.DIAMONDS, rank=Rank.EIGHT)
        ]
        player3.cards = [
            Card(suit=Suit.HEARTS, rank=Rank.TWO),
            Card(suit=Suit.CLUBS, rank=Rank.NINE),
            Card(suit=Suit.SPADES, rank=Rank.TEN)
        ]
        player4.cards = [
            Card(suit=Suit.CLUBS, rank=Rank.ACE),
            Card(suit=Suit.DIAMONDS, rank=Rank.KING),
            Card(suit=Suit.SPADES, rank=Rank.QUEEN)
        ]
        
        # 添加玩家到房间
        game_state.room.players = [player1, player2, player3, player4]
        game_state.current_player = PlayerPosition.NORTH
        
        return game_state
    
    # 测试场景：甩牌失败后自动使用强制要求的牌
    print("\n场景1：尝试甩牌红桃3♥和梅花6♣ (甩牌失败，因为player2有4♥)")
    game_state = create_new_game_state()
    
    # 设置选中卡牌为3♥和6♣，模拟玩家尝试甩牌
    game_state.selected_cards = [game_state.room.players[0].cards[0], game_state.room.players[0].cards[1]]
    print(f"选中卡牌: {[str(card) for card in game_state.selected_cards]}")
    
    # 执行自动出牌
    result = game_state.auto_play()
    print(f"自动出牌结果: {result}")
    
    # 验证结果
    if result["success"] and "played_cards" in result:
        played_cards = result["played_cards"]
        print(f"实际打出的牌: {[str(card) for card in played_cards]}")
        # 应该只打出3♥，因为甩牌失败后被强制要求出最小的红桃牌
        if len(played_cards) == 1 and played_cards[0].rank == "3" and played_cards[0].suit == "♥":
            print("✅ 测试通过：甩牌失败后自动使用了强制要求的牌 (3♥)")
        else:
            print("❌ 测试失败：没有使用强制要求的牌")
    else:
        print("❌ 测试失败：自动出牌失败")
    
    print("\n=== 测试完成 ===")


if __name__ == "__main__":
    test_slingshot_fix()
