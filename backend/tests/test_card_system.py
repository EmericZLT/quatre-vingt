"""
测试纸牌系统
"""
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from app.game.card_system import CardSystem
from app.models.game import Suit, Rank, Card

def test_card_system():
    """测试纸牌系统功能"""
    print("Testing Card System...")
    
    # 创建纸牌系统
    card_system = CardSystem()
    
    # 测试创建牌组
    print("\n1. Testing deck creation...")
    deck = card_system.create_deck()
    print(f"Deck size: {len(deck)}")
    print(f"First 5 cards: {[str(card) for card in deck[:5]]}")
    
    # 测试洗牌
    print("\n2. Testing shuffle...")
    original_first = str(deck[0])
    card_system.shuffle_deck()
    shuffled_first = str(deck[0])
    print(f"Original first card: {original_first}")
    print(f"Shuffled first card: {shuffled_first}")
    print(f"Shuffled: {original_first != shuffled_first}")
    
    # 测试发牌
    print("\n3. Testing deal cards...")
    hands = card_system.deal_cards()
    print(f"North cards: {len(hands['north'])}")
    print(f"East cards: {len(hands['east'])}")
    print(f"South cards: {len(hands['south'])}")
    print(f"West cards: {len(hands['west'])}")
    print(f"Bottom cards: {len(hands['bottom'])}")
    print(f"Total cards: {sum(len(hand) for hand in hands.values())}")
    
    # 测试级牌判断
    print("\n4. Testing level card detection...")
    card_system.set_level(10)
    level_card = None
    for card in deck:
        if card.rank == Rank.TEN and not card.is_joker:
            level_card = card
            break
    
    if level_card:
        print(f"Level card (10): {str(level_card)}")
        print(f"Is level card: {card_system.is_level_card(level_card)}")
    
    # 测试分数计算
    print("\n5. Testing card scoring...")
    test_cards = [
        Card(suit=Suit.HEARTS, rank=Rank.FIVE),
        Card(suit=Suit.SPADES, rank=Rank.TEN),
        Card(suit=Suit.CLUBS, rank=Rank.KING),
        Card(suit=Suit.DIAMONDS, rank=Rank.THREE)
    ]
    
    for card in test_cards:
        score = card_system.get_card_score(card)
        print(f"Card {str(card)}: {score} points")
    
    # 测试牌大小比较
    print("\n6. Testing card comparison...")
    card1 = Card(suit=Suit.HEARTS, rank=Rank.TEN)
    card2 = Card(suit=Suit.SPADES, rank=Rank.TEN)
    card3 = Card(suit=Suit.HEARTS, rank=Rank.ACE)
    
    print(f"Comparing {str(card1)} vs {str(card2)}: {card_system.compare_cards(card1, card2)}")
    print(f"Comparing {str(card1)} vs {str(card3)}: {card_system.compare_cards(card1, card3)}")
    
    # 测试主牌比较
    print("\n7. Testing trump card comparison...")
    trump_suit = Suit.HEARTS
    trump_card = Card(suit=Suit.HEARTS, rank=Rank.THREE)
    normal_card = Card(suit=Suit.SPADES, rank=Rank.ACE)
    
    print(f"Trump card {str(trump_card)} vs normal card {str(normal_card)}: {card_system.compare_cards(trump_card, normal_card, trump_suit)}")
    
    print("\nCard system test completed!")

if __name__ == "__main__":
    test_card_system()
