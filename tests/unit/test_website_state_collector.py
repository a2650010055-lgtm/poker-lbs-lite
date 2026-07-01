import pytest

from app.collector.sample_website_states import get_sample_website_state
from app.collector.website_state import (
    CollectedStateError,
    convert_website_state_to_raw_state,
)


def test_check_sample_converts_to_raw_state():
    raw = convert_website_state_to_raw_state(get_sample_website_state("check"))

    assert raw == {
        "mode": "single",
        "table_size": 2,
        "street": "flop",
        "position": "BTN_vs_BB",
        "current_actor": "hero",
        "hero_seat": "hero",
        "known_hands": {"hero": ["Ah", "Kh"]},
        "unknown_seats": ["villain"],
        "board": ["Kc", "8d", "3s"],
        "pot": 100,
        "effective_stacks": {"hero": 900, "villain": 900},
        "action_history": [{"player": "BB", "action": "check"}],
        "objective": "actor_ev",
    }


def test_bet_sample_converts_to_raw_state():
    raw = convert_website_state_to_raw_state(get_sample_website_state("bet"))

    assert raw["known_hands"] == {"hero": ["Qh", "Jh"]}
    assert raw["pot"] == 150
    assert raw["effective_stacks"] == {"hero": 850, "villain": 850}
    assert raw["action_history"] == [
        {"player": "BB", "action": "bet", "size": 50}
    ]


def test_missing_required_field_returns_readable_error():
    state = get_sample_website_state("check")
    del state["hero_cards"]

    with pytest.raises(CollectedStateError, match="INVALID_COLLECTED_STATE: hero_cards"):
        convert_website_state_to_raw_state(state)


def test_unsupported_action_returns_readable_error():
    state = get_sample_website_state("check")
    state["facing_action"]["action"] = "all_in"

    with pytest.raises(
        CollectedStateError,
        match="UNSUPPORTED_COLLECTED_STATE: facing_action.action",
    ):
        convert_website_state_to_raw_state(state)


def test_unknown_sample_scenario_returns_readable_error():
    with pytest.raises(CollectedStateError, match="UNSUPPORTED_COLLECTED_SCENARIO"):
        get_sample_website_state("river")
