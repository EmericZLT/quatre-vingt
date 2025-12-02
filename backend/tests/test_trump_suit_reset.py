"""
测试trump_suit在连续游戏中是否正确重置
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.models.game import GameRoom, Suit, Player, PlayerPosition
from app.game.game_state import GameState


def test_trump_suit_reset_between_rounds():
    """
    测试连续两轮游戏中trump_suit的重置
    
    场景：
    1. 第一轮：黑桃为主
    2. 第二轮：无主（用对王亮主）
    3. 检查第二轮开始时trump_suit是否被正确清空
    """
    print("\n" + "="*60)
    print("测试trump_suit在连续游戏中的重置")
    print("="*60)
    
    # 创建游戏房间
    room = GameRoom(
        id="test_room",
        name="Test Room",
        host_id="player1"
    )
    game_state = GameState(room)
    
    # 模拟第一轮游戏：黑桃为主
    print("\n第一轮游戏：")
    print(f"  初始 trump_suit: {game_state.trump_suit}")
    
    # 设置黑桃为主
    game_state.trump_suit = Suit.SPADES
    game_state.room.trump_suit = Suit.SPADES
    print(f"  设置后 trump_suit: {game_state.trump_suit}")
    
    # 模拟第二轮游戏开始（调用start_game）
    print("\n第二轮游戏开始（调用start_game后）：")
    
    # 添加4个玩家并准备开始游戏
    for i, pos in enumerate([PlayerPosition.NORTH, PlayerPosition.EAST, PlayerPosition.SOUTH, PlayerPosition.WEST]):
        player = Player(id=f"player{i+1}", name=f"Player{i+1}", position=pos)
        room.players.append(player)
        game_state.players_ready_to_start.add(f"player{i+1}")
    
    # 调用start_game()
    game_state.start_game()
    
    print(f"  trump_suit: {game_state.trump_suit}")
    print(f"  期望: None（应该被清空）")
    print(f"  实际: {game_state.trump_suit}")
    
    if game_state.trump_suit is not None:
        print(f"  ❌ 错误：trump_suit没有被清空！仍然是 {game_state.trump_suit}")
    else:
        print(f"  ✓ 正确：trump_suit已被清空")
    
    # 检查start_game是否清空trump_suit
    print("\n检查start_game()方法：")
    with open("/Users/zhangleiting/Documents/github/quatre-vingt/backend/app/game/game_state.py", "r") as f:
        content = f.read()
        if "def start_game" in content:
            start_game_section = content[content.find("def start_game"):content.find("def start_game") + 2000]
            if "self.trump_suit = None" in start_game_section:
                print("  ✓ start_game()中有重置trump_suit的代码")
            else:
                print("  ❌ start_game()中没有重置trump_suit的代码")
    
    # 检查start_next_round是否清空trump_suit
    print("\n检查start_next_round()方法：")
    with open("/Users/zhangleiting/Documents/github/quatre-vingt/backend/app/game/game_state.py", "r") as f:
        content = f.read()
        if "def start_next_round" in content:
            start_next_round_section = content[content.find("def start_next_round"):content.find("def start_next_round") + 2000]
            if "self.trump_suit = None" in start_next_round_section:
                print("  ✓ start_next_round()中有重置trump_suit的代码")
            else:
                print("  ❌ start_next_round()中没有重置trump_suit的代码")
    
    print("\n" + "="*60)
    print("结论：")
    print("  如果start_game()没有重置trump_suit，")
    print("  那么在第一局游戏结束后，第二局开始时，")
    print("  trump_suit仍然保留上一局的值（例如黑桃），")
    print("  这会导致CardPlayingSystem使用错误的trump_suit初始化！")
    print("="*60)


if __name__ == "__main__":
    test_trump_suit_reset_between_rounds()

