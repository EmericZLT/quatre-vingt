"""
测试游戏状态管理
"""
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from app.game.game_state import GameState
from app.models.game import GameRoom, Player, PlayerPosition, Suit, Rank, Card
from app.game.card_system import CardSystem

def test_game_state():
    """测试游戏状态管理"""
    print("Testing Game State Management...")
    
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
    
    print(f"Room created with {len(room.players)} players")
    print(f"Can start: {room.can_start}")
    
    # 创建游戏状态
    game_state = GameState(room)
    print(f"Initial game phase: {game_state.game_phase}")
    
    # 测试开始游戏
    print("\n1. Testing start game...")
    success = game_state.start_game()
    print(f"Game started: {success}")
    print(f"Game phase: {game_state.game_phase}")
    print(f"Room status: {room.status}")
    
    if success:
        # 检查每个玩家的牌数
        print("\n2. Testing card distribution...")
        for player in room.players:
            print(f"{player.name} ({player.position.value}): {len(player.cards)} cards")
        
        # 检查底牌
        print(f"Bottom cards: {len(game_state.bottom_cards)} cards")
        print(f"Dealer has bottom: {game_state.dealer_has_bottom}")
        
        # 测试设置主牌
        print("\n3. Testing trump suit setting...")
        trump_set = game_state.set_trump_suit(Suit.HEARTS)
        print(f"Trump suit set: {trump_set}")
        print(f"Trump suit: {game_state.trump_suit}")
        print(f"Game phase: {game_state.game_phase}")
        
        # 检查庄家获得底牌后的牌数
        print("\n4. Testing dealer bottom cards...")
        dealer = game_state.get_dealer()
        if dealer:
            print(f"Dealer {dealer.name} cards: {len(dealer.cards)}")
            print(f"Dealer has bottom: {game_state.dealer_has_bottom}")
            print(f"Bottom cards count: {len(game_state.bottom_cards)}")
        
        # 测试出牌
        print("\n5. Testing card play...")
        if room.players:
            player = room.players[0]
            if player.cards:
                card = player.cards[0]
                print(f"Player {player.name} playing card: {str(card)}")
                play_success = game_state.play_card(player.id, card)
                print(f"Card played: {play_success}")
                print(f"Player cards remaining: {len(player.cards)}")
                print(f"Current trick: {len(game_state.current_trick)} cards")
        
        # 测试游戏状态获取
        print("\n6. Testing game status...")
        status = game_state.get_game_status()
        print(f"Game status keys: {list(status.keys())}")
        print(f"Players in status: {len(status['players'])}")
        print(f"Scores: {status['scores']}")
    
    print("\nGame state test completed!")

if __name__ == "__main__":
    test_game_state()
