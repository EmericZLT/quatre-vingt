"""
测试完整的出牌逻辑
"""
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from app.game.card_playing import CardPlayingSystem, CardType
from app.game.card_system import CardSystem
from app.models.game import Suit, Rank, Card, PlayerPosition

def test_complete_card_playing():
    """测试完整的出牌逻辑"""
    print("Testing Complete Card Playing Logic...")
    
    # 创建出牌系统（打10，主牌花色为红桃）
    card_system = CardSystem()
    card_system.current_level = 10
    playing_system = CardPlayingSystem(card_system, trump_suit=Suit.HEARTS)
    
    print(f"Current level: {playing_system.card_system.current_level}")
    print(f"Trump suit: {playing_system.trump_suit}")
    
    # 测试1：基本跟牌规则
    print("\n1. Testing basic follow rules...")
    # 领出黑桃A
    lead_card = Card(suit=Suit.SPADES, rank=Rank.ACE, value=14)
    player_cards = [lead_card, Card(suit=Suit.HEARTS, rank=Rank.KING, value=13)]
    
    result = playing_system.play_card(PlayerPosition.NORTH, lead_card, player_cards)
    print(f"Lead card result: {result.success}")
    
    # 跟牌：有黑桃必须出黑桃
    follow_card = Card(suit=Suit.SPADES, rank=Rank.KING, value=13)
    follow_player_cards = [follow_card, Card(suit=Suit.SPADES, rank=Rank.QUEEN, value=12)]
    
    result = playing_system.play_card(PlayerPosition.EAST, follow_card, follow_player_cards)
    print(f"Follow card result: {result.success}")
    
    # 测试2：将吃规则
    print("\n2. Testing trump rules...")
    # 重置系统
    playing_system._reset_trick()
    
    # 领出黑桃A
    lead_card = Card(suit=Suit.SPADES, rank=Rank.ACE, value=14)
    player_cards = [lead_card, Card(suit=Suit.HEARTS, rank=Rank.KING, value=13)]
    
    result = playing_system.play_card(PlayerPosition.NORTH, lead_card, player_cards)
    print(f"Lead card result: {result.success}")
    
    # 将吃：没有黑桃，用主牌将吃
    trump_card = Card(suit=Suit.HEARTS, rank=Rank.QUEEN, value=12)  # 主牌1
    trump_card2 = Card(suit=Suit.CLUBS, rank=Rank.TEN, value=10)  # 主牌2，也是级牌
    trump_player_cards = [trump_card, trump_card2]  # 级牌
    
    result = playing_system.play_card(PlayerPosition.EAST, trump_card, trump_player_cards)
    print(f"Trump card result: {result.success}")
    
    # 测试3：超将吃
    print("\n3. Testing over trump...")
    # 继续出牌
    side_card = Card(suit=Suit.DIAMONDS, rank=Rank.JACK, value=11)
    side_player_cards = [side_card, Card(suit=Suit.CLUBS, rank=Rank.NINE, value=9)]
    
    result = playing_system.play_card(PlayerPosition.SOUTH, side_card, side_player_cards)
    print(f"Side card result: {result.success}")
    
    # 超将吃：用更大的主牌
    over_trump_card = Card(suit=Suit.CLUBS, rank=Rank.TEN, value=10)  # 级牌
    over_trump_player_cards = [over_trump_card, Card(suit=Suit.HEARTS, rank=Rank.ACE, value=14)]
    
    result = playing_system.play_card(PlayerPosition.WEST, over_trump_card, over_trump_player_cards)
    print(f"Over trump result: {result.success}")
    print(f"Trick winner: {result.winner}")
    
    # 测试4：对子跟牌规则
    print("\n4. Testing pair follow rules...")
    # 重置系统
    playing_system._reset_trick()
    
    # 领出对子
    pair_card1 = Card(suit=Suit.CLUBS, rank=Rank.KING, value=13)
    pair_card2 = Card(suit=Suit.CLUBS, rank=Rank.KING, value=13)
    pair_cards = [pair_card1, pair_card2, Card(suit=Suit.DIAMONDS, rank=Rank.ACE, value=14)]
    
    result = playing_system.play_card(PlayerPosition.NORTH, pair_card1, pair_cards)
    print(f"Pair lead result: {result.success}")
    
    # 测试5：拖拉机跟牌规则
    print("\n5. Testing tractor follow rules...")
    # 重置系统
    playing_system._reset_trick()
    
    # 领出拖拉机（99JJ，当级牌是10时）
    tractor_cards = [
        Card(suit=Suit.SPADES, rank=Rank.NINE, value=9),
        Card(suit=Suit.SPADES, rank=Rank.NINE, value=9),
        Card(suit=Suit.SPADES, rank=Rank.JACK, value=11),
        Card(suit=Suit.SPADES, rank=Rank.JACK, value=11)
    ]
    
    result = playing_system.play_card(PlayerPosition.NORTH, tractor_cards[0], tractor_cards)
    print(f"Tractor lead result: {result.success}")
    
    # 测试6：判断一圈获胜者
    print("\n6. Testing trick winner determination...")
    # 重置系统
    playing_system._reset_trick()
    
    # 模拟一圈出牌（逆时针顺序）
    cards = [
        (PlayerPosition.NORTH, Card(suit=Suit.SPADES, rank=Rank.ACE, value=14)),
        (PlayerPosition.WEST, Card(suit=Suit.SPADES, rank=Rank.KING, value=13)),
        (PlayerPosition.SOUTH, Card(suit=Suit.HEARTS, rank=Rank.QUEEN, value=12)),  # 主牌
        (PlayerPosition.EAST, Card(suit=Suit.CLUBS, rank=Rank.TEN, value=10))  # 级牌
    ]
    
    for player, card in cards:
        playing_system.current_trick.append((player, card))
    
    winner = playing_system._determine_trick_winner()
    print(f"Trick winner: {winner}")
    
    # 测试7：当前圈状态
    print("\n7. Testing trick status...")
    status = playing_system.get_trick_status()
    print(f"Trick leader: {status['trick_leader']}")
    print(f"Led suit: {status['led_suit']}")
    print(f"Led card type: {status['led_card_type']}")
    print(f"Trick count: {status['trick_count']}")
    
    print("\nComplete card playing test completed!")

if __name__ == "__main__":
    test_complete_card_playing()
