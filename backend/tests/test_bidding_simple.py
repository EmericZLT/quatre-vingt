"""
简化测试亮主系统
"""
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from app.game.bidding_system import BiddingSystem, BidType
from app.models.game import Suit, Rank, Card

def test_bidding_simple():
    """简化测试亮主系统"""
    print("Testing Bidding System...")
    
    # 创建亮主系统（打10）
    bidding_system = BiddingSystem(current_level=10)
    print(f"Current level: {bidding_system.current_level}")
    print(f"Bidding phase: {bidding_system.bidding_phase}")
    
    # 测试单张级牌亮主
    print("\n1. Testing single level card bid...")
    level_card = Card(suit=Suit.HEARTS, rank=Rank.TEN, value=10)
    result = bidding_system.make_bid("player1", [level_card])
    print(f"Single level bid success: {result['success']}")
    print(f"Single level bid message: {result['message']}")
    
    # 测试级牌对子反主
    print("\n2. Testing level pair bid...")
    level_pair = [
        Card(suit=Suit.SPADES, rank=Rank.TEN, value=10),
        Card(suit=Suit.SPADES, rank=Rank.TEN, value=10)
    ]
    result = bidding_system.make_bid("player2", level_pair)
    print(f"Level pair bid success: {result['success']}")
    print(f"Level pair bid message: {result['message']}")
    
    # 测试双小王反主
    print("\n3. Testing double small joker bid...")
    double_small_joker = [
        Card(suit=Suit.HEARTS, rank=Rank.SMALL_JOKER, value=15, is_joker=True),
        Card(suit=Suit.HEARTS, rank=Rank.SMALL_JOKER, value=15, is_joker=True)
    ]
    result = bidding_system.make_bid("player3", double_small_joker)
    print(f"Double small joker bid success: {result['success']}")
    print(f"Double small joker bid message: {result['message']}")
    
    # 测试双大王反主
    print("\n4. Testing double big joker bid...")
    double_big_joker = [
        Card(suit=Suit.SPADES, rank=Rank.BIG_JOKER, value=16, is_joker=True),
        Card(suit=Suit.SPADES, rank=Rank.BIG_JOKER, value=16, is_joker=True)
    ]
    result = bidding_system.make_bid("player4", double_big_joker)
    print(f"Double big joker bid success: {result['success']}")
    print(f"Double big joker bid message: {result['message']}")
    
    # 测试无效牌型
    print("\n5. Testing invalid bid...")
    invalid_cards = [Card(suit=Suit.HEARTS, rank=Rank.ACE, value=14)]
    result = bidding_system.make_bid("player5", invalid_cards)
    print(f"Invalid bid success: {result['success']}")
    print(f"Invalid bid message: {result['message']}")
    
    # 测试亮主状态
    print("\n6. Testing bidding status...")
    status = bidding_system.get_bidding_status()
    print(f"Bidding phase: {status['bidding_phase']}")
    print(f"Total bids: {status['total_bids']}")
    print(f"Current level: {status['current_level']}")
    
    # 测试结束亮主
    print("\n7. Testing finish bidding...")
    final_bid = bidding_system.finish_bidding()
    print(f"Final bid exists: {final_bid is not None}")
    print(f"Trump suit: {bidding_system.get_trump_suit()}")
    
    print("\nBidding system test completed!")

if __name__ == "__main__":
    test_bidding_simple()
