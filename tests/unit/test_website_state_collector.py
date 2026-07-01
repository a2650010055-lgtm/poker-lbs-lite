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


def test_invalid_root_state_returns_readable_error():
    with pytest.raises(CollectedStateError, match="INVALID_COLLECTED_STATE: root"):
        convert_website_state_to_raw_state([])


@pytest.mark.parametrize(
    ("field", "value", "message"),
    [
        ("street", "turn", "UNSUPPORTED_COLLECTED_STATE: street"),
        ("position", "CO_vs_BB", "UNSUPPORTED_COLLECTED_STATE: position"),
        ("current_actor", "villain", "UNSUPPORTED_COLLECTED_STATE: current_actor"),
    ],
)
def test_unsupported_stable_fields_return_readable_error(field, value, message):
    state = get_sample_website_state("check")
    state[field] = value

    with pytest.raises(CollectedStateError, match=message):
        convert_website_state_to_raw_state(state)


@pytest.mark.parametrize(
    ("path", "value", "message"),
    [
        (("hero_cards",), ["Ah"], "INVALID_COLLECTED_STATE: hero_cards"),
        (("board_cards",), ["Kc", "8d"], "INVALID_COLLECTED_STATE: board_cards"),
        (("pot",), "100", "INVALID_COLLECTED_STATE: pot"),
        (("stacks",), [], "INVALID_COLLECTED_STATE: stacks"),
        (("stacks", "hero"), "900", "INVALID_COLLECTED_STATE: stacks.hero"),
        (("stacks", "villain"), "900", "INVALID_COLLECTED_STATE: stacks.villain"),
        (("facing_action",), [], "INVALID_COLLECTED_STATE: facing_action"),
    ],
)
def test_malformed_fields_return_readable_error(path, value, message):
    state = get_sample_website_state("check")
    _set_nested_value(state, path, value)

    with pytest.raises(CollectedStateError, match=message):
        convert_website_state_to_raw_state(state)


@pytest.mark.parametrize("size", [0, -1, "50"])
def test_invalid_bet_size_returns_readable_error(size):
    state = get_sample_website_state("bet")
    state["facing_action"]["size"] = size

    with pytest.raises(
        CollectedStateError,
        match="INVALID_COLLECTED_STATE: facing_action.size",
    ):
        convert_website_state_to_raw_state(state)


def test_unsupported_player_returns_readable_error():
    state = get_sample_website_state("check")
    state["facing_action"]["player"] = "SB"

    with pytest.raises(
        CollectedStateError,
        match="UNSUPPORTED_COLLECTED_STATE: facing_action.player",
    ):
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


def test_sample_website_state_returns_deep_copy():
    state = get_sample_website_state("bet")
    state["hand_id"] = "mutated"
    state["hero_cards"][0] = "2c"
    state["board_cards"].append("4h")
    state["facing_action"]["size"] = 999

    fresh_state = get_sample_website_state("bet")

    assert fresh_state["hand_id"] == "demo-bet-001"
    assert fresh_state["hero_cards"] == ["Qh", "Jh"]
    assert fresh_state["board_cards"] == ["Kc", "8d", "3s"]
    assert fresh_state["facing_action"] == {
        "player": "BB",
        "action": "bet",
        "size": 50,
    }


def _set_nested_value(state, path, value):
    target = state
    for key in path[:-1]:
        target = target[key]
    target[path[-1]] = value
