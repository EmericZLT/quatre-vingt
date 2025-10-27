"""
测试拖拉机逻辑
"""
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from app.game.tractor_logic import TractorLogic
from app.models.game import Suit, Rank, Card

def test_tractor_logic():
    """测试拖拉机逻辑"""
    print("Testing Tractor Logic...")
    
    # 创建拖拉机逻辑（打10）
    tractor_logic = TractorLogic(current_level=10)
    print(f"Current level: {tractor_logic.current_level}")
    print(f"Level rank: {tractor_logic.level_rank}")
    
    # 测试1：级牌为10时的拖拉机
    print("\n1. Testing tractor with level 10...")
    # 9和J相邻（当级牌是10时）
    tractor_cards = [
        Card(suit=Suit.SPADES, rank=Rank.NINE, value=9),
        Card(suit=Suit.SPADES, rank=Rank.NINE, value=9),
        Card(suit=Suit.SPADES, rank=Rank.JACK, value=11),
        Card(suit=Suit.SPADES, rank=Rank.JACK, value=11)
    ]
    
    is_tractor = tractor_logic.is_tractor(tractor_cards)
    print(f"99JJ tractor (level 10): {is_tractor}")
    
    if is_tractor:
        info = tractor_logic.get_tractor_info(tractor_cards)
        print(f"Tractor is valid: {info['is_tractor']}")
        print(f"Tractor length: {info['tractor_length']}")
    
    # 测试2：级牌为8时的拖拉机
    print("\n2. Testing tractor with level 8...")
    tractor_logic_8 = TractorLogic(current_level=8)
    # 7和9相邻（当级牌是8时）
    tractor_cards_8 = [
        Card(suit=Suit.HEARTS, rank=Rank.SEVEN, value=7),
        Card(suit=Suit.HEARTS, rank=Rank.SEVEN, value=7),
        Card(suit=Suit.HEARTS, rank=Rank.NINE, value=9),
        Card(suit=Suit.HEARTS, rank=Rank.NINE, value=9)
    ]
    
    is_tractor_8 = tractor_logic_8.is_tractor(tractor_cards_8)
    print(f"7799 tractor (level 8): {is_tractor_8}")
    
    # 测试3：非拖拉机
    print("\n3. Testing non-tractor...")
    non_tractor_cards = [
        Card(suit=Suit.CLUBS, rank=Rank.ACE, value=14),
        Card(suit=Suit.CLUBS, rank=Rank.ACE, value=14),
        Card(suit=Suit.CLUBS, rank=Rank.KING, value=13),
        Card(suit=Suit.CLUBS, rank=Rank.KING, value=13)
    ]
    
    is_non_tractor = tractor_logic.is_tractor(non_tractor_cards)
    print(f"AAKK non-tractor: {is_non_tractor}")
    
    # 测试4：单对子
    print("\n4. Testing single pair...")
    single_pair = [
        Card(suit=Suit.DIAMONDS, rank=Rank.QUEEN, value=12),
        Card(suit=Suit.DIAMONDS, rank=Rank.QUEEN, value=12)
    ]
    
    is_single_pair = tractor_logic.is_tractor(single_pair)
    print(f"QQ single pair: {is_single_pair}")
    
    # 测试5：相邻关系检查
    print("\n5. Testing adjacency check...")
    # 当级牌是10时，9和J应该相邻
    adjacent_9_j = tractor_logic._are_adjacent(Rank.NINE, Rank.JACK)
    print(f"9 and J adjacent (level 10): {adjacent_9_j}")
    
    # 当级牌是10时，8和J不应该相邻
    not_adjacent_8_j = tractor_logic._are_adjacent(Rank.EIGHT, Rank.JACK)
    print(f"8 and J not adjacent (level 10): {not not_adjacent_8_j}")
    
    print("\nTractor logic test completed!")

if __name__ == "__main__":
    test_tractor_logic()
