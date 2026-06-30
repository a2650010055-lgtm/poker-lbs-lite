from app.engine.action_generator import ActionGenerator
import pytest

from app.schema.actions import ALL_IN, BET_33, BET_75, CALL, CHECK, FOLD, RAISE_3X
from app.schema.state import NormalizedState


def make_state(action_history):
    return NormalizedState(
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
        action_history=action_history,
        objective="actor_ev",
        state_hash="x",
    )


def test_no_bet_actions_when_no_open_bet_on_current_street():
    actions = ActionGenerator().legal_actions(make_state([{"player": "BB", "action": "check"}]))
    assert actions == [CHECK, BET_33, BET_75]


def test_facing_bet_actions_when_villain_bet_exists():
    actions = ActionGenerator().legal_actions(make_state([{"player": "BB", "action": "bet", "size": 50}]))
    assert actions == [FOLD, CALL, RAISE_3X]


def test_facing_bet_actions_when_villain_uses_sized_bet_action():
    actions = ActionGenerator().legal_actions(make_state([{"player": "BB", "action": BET_33}]))
    assert actions == [FOLD, CALL, RAISE_3X]


def test_all_in_is_rejected_in_v01_action_generator():
    with pytest.raises(ValueError, match="UNSUPPORTED_ACTION"):
        ActionGenerator().legal_actions(make_state([{"player": "BB", "action": ALL_IN}]))


def test_prior_all_in_is_rejected_in_v01_action_generator():
    with pytest.raises(ValueError, match="UNSUPPORTED_ACTION"):
        ActionGenerator().legal_actions(
            make_state(
                [
                    {"player": "BB", "action": ALL_IN},
                    {"player": "hero", "action": CALL},
                    {"player": "BB", "action": BET_33},
                ]
            )
        )
