import pytest

from app.schema.cards import Card, validate_unique_cards


def test_valid_card_parses_rank_and_suit():
    card = Card.from_str("Ah")
    assert card.rank == "A"
    assert card.suit == "h"
    assert str(card) == "Ah"


def test_invalid_card_rejected():
    with pytest.raises(ValueError, match="INVALID_CARD"):
        Card.from_str("1x")


def test_duplicate_cards_rejected():
    with pytest.raises(ValueError, match="DUPLICATE_CARD"):
        validate_unique_cards(["Ah", "Ah", "Kc"])
