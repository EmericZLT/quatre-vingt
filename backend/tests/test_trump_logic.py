"""
测试将吃逻辑
"""
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from app.game.trump_logic import TrumpLogic
from app.game.card_comparison import CardComparison
from app.game.tractor_logic import TractorLogic
from app.game.card_system import CardSystem
from app.models.game import Suit, Rank, Card

def test_trump_logic():
    """测试将吃逻辑"""
    print("Testing Trump Logic...")
    
    # 创建系统（打10，主牌花色为红桃）
    card_system = CardSystem()
    card_system.current_level = 10
    comparison = CardComparison(card_system, trump_suit=Suit.HEARTS)
    tractor_logic = TractorLogic(current_level=10)
    trump_logic = TrumpLogic(comparison, tractor_logic)
    
    print(f"Current level: {trump_logic.current_level}")
    print(f"Trump suit: {trump_logic.trump_suit}")
    
    # 测试1：有该花色不能将吃
    print("\n1. Testing cannot trump when has led suit...")
    player_cards = [
        Card(suit=Suit.SPADES, rank=Rank.ACE, value=14),  # 有黑桃
        Card(suit=Suit.HEARTS, rank=Rank.KING, value=13),  # 主牌
        Card(suit=Suit.CLUBS, rank=Rank.TEN, value=10)    # 级牌
    ]
    
    can_trump = trump_logic.can_trump(player_cards, Suit.SPADES, "single")
    print(f"Can trump when has led suit: {can_trump}")
    
    # 测试2：没有该花色可以将吃
    print("\n2. Testing can trump when no led suit...")
    player_cards_no_suit = [
        Card(suit=Suit.HEARTS, rank=Rank.KING, value=13),  # 主牌
        Card(suit=Suit.CLUBS, rank=Rank.TEN, value=10),   # 级牌
        Card(suit=Suit.DIAMONDS, rank=Rank.QUEEN, value=12)
    ]
    
    can_trump = trump_logic.can_trump(player_cards_no_suit, Suit.SPADES, "single")
    print(f"Can trump when no led suit: {can_trump}")
    
    # 测试3：没有主牌不能将吃
    print("\n3. Testing cannot trump when no trump cards...")
    player_cards_no_trump = [
        Card(suit=Suit.DIAMONDS, rank=Rank.QUEEN, value=12),
        Card(suit=Suit.CLUBS, rank=Rank.JACK, value=11)
    ]
    
    can_trump = trump_logic.can_trump(player_cards_no_trump, Suit.SPADES, "single")
    print(f"Can trump when no trump cards: {can_trump}")
    
    # 测试4：对子将吃
    print("\n4. Testing pair trump...")
    player_cards_pair = [
        Card(suit=Suit.HEARTS, rank=Rank.KING, value=13),
        Card(suit=Suit.HEARTS, rank=Rank.KING, value=13),  # 主牌对子
        Card(suit=Suit.CLUBS, rank=Rank.TEN, value=10)
    ]
    
    can_trump_pair = trump_logic.can_trump(player_cards_pair, Suit.SPADES, "pair")
    print(f"Can trump pair: {can_trump_pair}")
    
    # 测试5：获取将吃选项
    print("\n5. Testing get trump options...")
    trump_options = trump_logic.get_trump_options(player_cards_no_suit, Suit.SPADES, "single")
    print(f"Trump options count: {len(trump_options)}")
    
    # 测试6：超将吃
    print("\n6. Testing over trump...")
    current_trump = Card(suit=Suit.HEARTS, rank=Rank.KING, value=13)
    new_trump = Card(suit=Suit.CLUBS, rank=Rank.TEN, value=10)  # 级牌
    
    can_over_trump = trump_logic.can_over_trump(current_trump, new_trump)
    print(f"Can over trump: {can_over_trump}")
    
    # 测试7：将吃信息
    print("\n7. Testing trump info...")
    trump_info = trump_logic.get_trump_info(player_cards_no_suit, Suit.SPADES, "single")
    print(f"Trump info: {trump_info}")
    
    print("\nTrump logic test completed!")

if __name__ == "__main__":
    test_trump_logic()
