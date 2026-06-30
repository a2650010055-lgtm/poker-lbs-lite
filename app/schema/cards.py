from dataclasses import dataclass

RANKS = set("23456789TJQKA")
SUITS = set("cdhs")


@dataclass(frozen=True)
class Card:
    rank: str
    suit: str

    @classmethod
    def from_str(cls, value: str) -> "Card":
        if len(value) != 2:
            raise ValueError(f"INVALID_CARD: {value}")
        rank, suit = value[0], value[1]
        if rank not in RANKS or suit not in SUITS:
            raise ValueError(f"INVALID_CARD: {value}")
        return cls(rank=rank, suit=suit)

    def __str__(self) -> str:
        return f"{self.rank}{self.suit}"


def validate_unique_cards(cards: list[str]) -> None:
    normalized = [str(Card.from_str(card)) for card in cards]
    if len(normalized) != len(set(normalized)):
        raise ValueError("DUPLICATE_CARD")
