import pytest

from app.collector.window_state_reader import WindowStateReader
from app.schema.state import NormalizedState
from app.services.analysis_service import normalize_raw_state


def _raw_state(**overrides):
    raw = {
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
    raw.update(overrides)
    return raw


def test_normalized_state_keeps_current_hand_fields():
    state = NormalizedState(
        mode="single",
        table_size=2,
        street="flop",
        position="BTN_vs_BB",
        current_actor="hero",
        hero_seat="hero",
        team_seats=["hero"],
        known_hands={"hero": ["Ah", "Kh"]},
        unknown_seats=["villain"],
        board=["Kc", "8d", "3s"],
        pot=100.0,
        effective_stacks={"hero": 900.0, "villain": 900.0},
        action_history=[
            {"player": "BTN", "action": "raise", "size": 2.5},
            {"player": "BB", "action": "call"},
            {"player": "BB", "action": "check"},
        ],
        objective="actor_ev",
        state_hash="abc",
    )
    assert state.street == "flop"
    assert state.known_hands["hero"] == ["Ah", "Kh"]


def test_normalize_raw_state_validates_cards_and_hashes_state():
    raw = _raw_state()
    state = normalize_raw_state(raw)
    assert state.state_hash
    assert state.team_seats == ["hero"]
    assert state.pot == 100.0


def test_normalize_raw_state_copies_mutable_raw_collections():
    raw = _raw_state(team_seats=["hero"])
    state = normalize_raw_state(raw)

    raw["known_hands"]["hero"].append("Qh")
    raw["board"].append("2c")
    raw["team_seats"].append("villain")
    raw["unknown_seats"].append("observer")
    raw["effective_stacks"]["hero"] = 1
    raw["action_history"][0]["action"] = "raise"
    raw["action_history"].append({"player": "hero", "action": "bet"})

    assert state.known_hands == {"hero": ["Ah", "Kh"]}
    assert state.board == ["Kc", "8d", "3s"]
    assert state.team_seats == ["hero"]
    assert state.unknown_seats == ["villain"]
    assert state.effective_stacks == {"hero": 900.0, "villain": 900.0}
    assert state.action_history == [{"player": "BB", "action": "check"}]


def test_normalize_raw_state_ignores_incoming_state_hash():
    first_state = normalize_raw_state(_raw_state(state_hash="incoming-one"))
    second_state = normalize_raw_state(_raw_state(state_hash="incoming-two"))

    assert first_state.state_hash == second_state.state_hash


def test_normalize_raw_state_rejects_duplicate_cards():
    raw = _raw_state(board=["Ah", "8d", "3s"])

    with pytest.raises(ValueError, match="DUPLICATE_CARD"):
        normalize_raw_state(raw)


def test_normalize_raw_state_rejects_invalid_cards():
    raw = _raw_state(board=["Kx", "8d", "3s"])

    with pytest.raises(ValueError, match="INVALID_CARD"):
        normalize_raw_state(raw)


def test_window_state_reader_returns_raw_dict():
    raw = {"table_size": 2}
    reader = WindowStateReader(lambda: raw)

    assert reader.read_raw_state() is raw


def test_window_state_reader_rejects_non_dict_state():
    reader = WindowStateReader(lambda: None)

    with pytest.raises(ValueError, match="COLLECTOR_FAILED"):
        reader.read_raw_state()
