"""
测试牌大小比较逻辑
"""
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from app.game.card_comparison import CardComparison
from app.game.card_system import CardSystem
from app.models.game import Suit, Rank, Card

def test_card_comparison():
    """测试牌大小比较"""
    print("Testing Card Comparison Logic...")
    
    # 创建比大小系统（打10，主牌花色为红桃）
    card_system = CardSystem()
    comparison = CardComparison(card_system, trump_suit=Suit.HEARTS)
    
    print(f"Current level: {comparison.current_level}")
    print(f"Level rank: {comparison.level_rank}")
    print(f"Trump suit: {comparison.trump_suit}")
    
    # 测试1：大小王比较
    print("\n1. Testing joker comparison...")
    big_joker = Card(suit=Suit.SPADES, rank=Rank.BIG_JOKER, value=16, is_joker=True)
    small_joker = Card(suit=Suit.HEARTS, rank=Rank.SMALL_JOKER, value=15, is_joker=True)
    
    result = comparison.compare_cards(big_joker, small_joker)
    print(f"Big joker vs Small joker: {result} (1 means big joker wins)")
    
    # 测试2：主牌与副牌比较
    print("\n2. Testing trump vs side card...")
    trump_card = Card(suit=Suit.HEARTS, rank=Rank.ACE, value=14)  # 主牌花色
    side_card = Card(suit=Suit.SPADES, rank=Rank.ACE, value=14)  # 副牌花色
    
    result = comparison.compare_cards(trump_card, side_card)
    print(f"Trump card vs Side card: {result} (1 means trump wins)")
    
    # 测试3：级牌比较
    print("\n3. Testing level card comparison...")
    level_card = Card(suit=Suit.CLUBS, rank=Rank.TEN, value=10)  # 级牌
    normal_trump = Card(suit=Suit.HEARTS, rank=Rank.ACE, value=14)  # 普通主牌
    
    result = comparison.compare_cards(level_card, normal_trump)
    print(f"Level card vs Normal trump: {result} (1 means level card wins)")
    
    # 测试4：副牌比较
    print("\n4. Testing side card comparison...")
    ace_spades = Card(suit=Suit.SPADES, rank=Rank.ACE, value=14)
    king_spades = Card(suit=Suit.SPADES, rank=Rank.KING, value=13)
    
    result = comparison.compare_cards(ace_spades, king_spades)
    print(f"Ace vs King (same suit): {result} (1 means ace wins)")
    
    # 测试5：不同花色副牌比较
    print("\n5. Testing different suit side cards...")
    ace_spades = Card(suit=Suit.SPADES, rank=Rank.ACE, value=14)
    ace_clubs = Card(suit=Suit.CLUBS, rank=Rank.ACE, value=14)
    
    result = comparison.compare_cards(ace_spades, ace_clubs)
    print(f"Ace Spades vs Ace Clubs: {result} (0 means equal)")
    
    # 测试6：找到最大牌
    print("\n6. Testing find winner card...")
    test_cards = [
        Card(suit=Suit.SPADES, rank=Rank.KING, value=13),
        Card(suit=Suit.HEARTS, rank=Rank.ACE, value=14),  # 主牌
        Card(suit=Suit.CLUBS, rank=Rank.TEN, value=10),  # 级牌
        Card(suit=Suit.DIAMONDS, rank=Rank.QUEEN, value=12)
    ]
    
    winner = comparison.find_winner_card(test_cards)
    print(f"Winner card: {str(winner)}")
    
    # 测试7：牌等级信息
    print("\n7. Testing card rank info...")
    level_card = Card(suit=Suit.CLUBS, rank=Rank.TEN, value=10)
    trump_card = Card(suit=Suit.HEARTS, rank=Rank.ACE, value=14)
    side_card = Card(suit=Suit.SPADES, rank=Rank.KING, value=13)
    
    level_info = comparison.get_card_rank_info(level_card)
    trump_info = comparison.get_card_rank_info(trump_card)
    side_info = comparison.get_card_rank_info(side_card)
    
    print(f"Level card info: {level_info}")
    print(f"Trump card info: {trump_info}")
    print(f"Side card info: {side_info}")
    
    print("\nCard comparison test completed!")

if __name__ == "__main__":
    test_card_comparison()


