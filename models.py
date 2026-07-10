from dataclasses import dataclass, field
from enum import Enum

class ItemType(Enum):
    BRON = "bron"
    KLUCZ = "klucz"
    NARZEDZIE = "narzedzie"
    ZUZYWALNY = "uzywalny"
    NIEZNANY = "nieznany"

@dataclass
class Attack:
    name: str
    damage_min: int
    damage_max: int
    miss_chance: float = 0.0        # szansa chybienia (0.0 = zawsze trafia)

@dataclass
class Item:
    name: str
    type: ItemType
    value: int
    attacks: list[Attack] = field(default_factory=list)   # NOWE

@dataclass
class GameState:
    hp: int = 100
    inventory: list[Item] = field(default_factory=list)

@dataclass
class Enemy:
    name: str
    hp: int
    damage_min: int
    damage_max: int

@dataclass
class Response:
    text: str
    input_tokens: int
    output_tokens: int
    stop_reason: str
    combat_with: str | None = None


@dataclass
class Usage:
    total_cost: float = 0.0
    total_input_tokens: int = 0
    total_output_tokens: int = 0