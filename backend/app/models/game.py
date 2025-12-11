"""
Game data models
"""
from enum import Enum
from typing import List, Optional, Dict, Any
from pydantic import BaseModel
from datetime import datetime


class Suit(str, Enum):
    """Card suits"""
    SPADES = "♠"
    HEARTS = "♥"
    DIAMONDS = "♦"
    CLUBS = "♣"


class Rank(str, Enum):
    """Card ranks"""
    TWO = "2"
    THREE = "3"
    FOUR = "4"
    FIVE = "5"
    SIX = "6"
    SEVEN = "7"
    EIGHT = "8"
    NINE = "9"
    TEN = "10"
    JACK = "J"
    QUEEN = "Q"
    KING = "K"
    ACE = "A"
    SMALL_JOKER = "JOKER-B"
    BIG_JOKER = "JOKER-A"


class Card(BaseModel):
    """
    Playing card model
    suit: 可为空，JOKER无花色。普通牌为♠/♥/♣/♦。
    """
    suit: Optional[Suit] = None  # JOKER无花色
    rank: Rank
    value: int = 0
    is_joker: bool = False
    
    def __str__(self) -> str:
        if self.is_joker:
            # 用rank来区分大王小王
            if self.rank == Rank.BIG_JOKER:
                return "JOKER-A/大王"
            elif self.rank == Rank.SMALL_JOKER:
                return "JOKER-B/小王"
            return "JOKER"
        return f"{self.rank.value}{self.suit.value if self.suit else ''}"


class PlayerPosition(str, Enum):
    """Player positions"""
    NORTH = "north"
    SOUTH = "south"
    EAST = "east"
    WEST = "west"


class Player(BaseModel):
    """Player model"""
    id: str
    name: str
    position: PlayerPosition
    cards: List[Card] = []
    is_ready: bool = False
    score: int = 0
    token: Optional[str] = None


class GameStatus(str, Enum):
    """Game status"""
    WAITING = "waiting"
    PLAYING = "playing"
    FINISHED = "finished"


class GameRoom(BaseModel):
    """Game room model"""
    id: str
    name: str
    players: List[Player] = []
    status: GameStatus = GameStatus.WAITING
    current_level: int = 2
    dealer_position: PlayerPosition = PlayerPosition.NORTH
    trump_suit: Optional[Suit] = None
    created_at: datetime = datetime.now()
    owner_id: Optional[str] = None
    play_time_limit: int = 18  # 出牌等待时间（秒），默认18秒（中等）
    level_up_mode: str = "default"  # 升级模式："default"（滁州版）或"standard"（国标版）
    
    @property
    def is_full(self) -> bool:
        return len(self.players) >= 4
    
    @property
    def can_start(self) -> bool:
        return len(self.players) == 4 and all(player.is_ready for player in self.players)
