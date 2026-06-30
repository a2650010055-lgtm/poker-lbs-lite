from dataclasses import replace

import pytest

from app.config import ENGINE_VERSION
from app.engine.board_texture import classify_board
from app.engine.belief import BeliefModel
from app.engine.ev import estimate_action_ev
from app.engine.hand_evaluator import classify_made_hand
from app.engine.ranges import BTN_VS_BB_CALL_RANGE
from app.engine.strategy_tree import evaluate_actions
from app.schema.result import AnalysisResult
from app.schema.state import NormalizedState


def test_classify_top_pair_top_kicker():
    result = classify_made_hand(hero_hand=["Ah", "Kh"], board=["Kc", "8d", "3s"])
    assert result == "top_pair_top_kicker"


def test_classify_ace_high_top_pair_top_kicker():
    result = classify_made_hand(hero_hand=["Ah", "Kh"], board=["Ac", "8d", "3s"])
    assert result == "top_pair_top_kicker"


def test_classify_pocket_pair_as_pair():
    result = classify_made_hand(hero_hand=["Ah", "Ad"], board=["Kc", "8d", "3s"])
    assert result == "pair"


def test_classify_weak_top_pair_as_pair():
    result = classify_made_hand(hero_hand=["Ah", "2h"], board=["Ac", "8d", "3s"])
    assert result == "pair"


def test_classify_unpaired_hand_as_high_card():
    result = classify_made_hand(hero_hand=["Ah", "Qh"], board=["Kc", "8d", "3s"])
    assert result == "high_card"


def test_classify_k_high_dry_board():
    result = classify_board(["Kc", "8d", "3s"])
    assert "k_high" in result
    assert "dry" in result


def test_classify_wet_board():
    result = classify_board(["Kc", "Qc", "Js"])
    assert "wet" in result


def _normalized_state(position="BTN_vs_BB", unknown_seats=None):
    if unknown_seats is None:
        unknown_seats = ["villain"]

    return NormalizedState(
        mode="single",
        table_size=2,
        street="flop",
        position=position,
        current_actor="hero",
        hero_seat="hero",
        team_seats=["hero"],
        known_hands={"hero": ["Ah", "Kh"]},
        unknown_seats=unknown_seats,
        board=["Kc", "8d", "3s"],
        pot=100.0,
        effective_stacks={seat: 900.0 for seat in ["hero", *unknown_seats]},
        action_history=[{"player": "BB", "action": "check"}],
        objective="actor_ev",
        state_hash="x",
    )


def _normalized_state_facing_bet():
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
        action_history=[{"player": "BB", "action": "bet_33"}],
        objective="actor_ev",
        state_hash="x",
    )


def test_belief_returns_villain_range_for_btn_vs_bb():
    state = _normalized_state()
    ranges = BeliefModel().estimate_ranges(state)
    assert "villain" in ranges
    assert ranges["villain"]["KQs"] > 0
    assert ranges["villain"] == BTN_VS_BB_CALL_RANGE
    assert ranges["villain"] is not BTN_VS_BB_CALL_RANGE

    ranges["villain"]["KQs"] = 0.0

    assert BTN_VS_BB_CALL_RANGE["KQs"] == 0.8


def test_belief_returns_empty_range_for_unsupported_position():
    state = _normalized_state(position="CO_vs_BB")
    ranges = BeliefModel().estimate_ranges(state)
    assert ranges["villain"] == {}


def test_belief_returns_independent_ranges_for_multiple_unknown_seats():
    state = _normalized_state(unknown_seats=["villain", "villain2"])
    ranges = BeliefModel().estimate_ranges(state)

    assert ranges["villain"] == BTN_VS_BB_CALL_RANGE
    assert ranges["villain2"] == BTN_VS_BB_CALL_RANGE
    assert ranges["villain"] is not ranges["villain2"]
    assert ranges["villain"] is not BTN_VS_BB_CALL_RANGE
    assert ranges["villain2"] is not BTN_VS_BB_CALL_RANGE

    ranges["villain"]["KQs"] = 0.0

    assert ranges["villain2"]["KQs"] == 0.8
    assert BTN_VS_BB_CALL_RANGE["KQs"] == 0.8


def test_bet_ev_can_exceed_check_ev_for_top_pair_on_dry_board():
    check_ev = estimate_action_ev(
        action="check",
        pot=100.0,
        hand_class="top_pair_top_kicker",
        board_tags=["k_high", "rainbow", "dry"],
        facing_bet=False,
    )
    bet_ev = estimate_action_ev(
        action="bet_33",
        pot=100.0,
        hand_class="top_pair_top_kicker",
        board_tags=["k_high", "rainbow", "dry"],
        facing_bet=False,
    )
    assert bet_ev > check_ev


def test_strategy_tree_returns_no_bet_action_evs():
    ev = evaluate_actions(
        _normalized_state(),
        hand_class="top_pair_top_kicker",
        board_tags=["k_high", "rainbow", "dry"],
    )

    assert set(ev) == {"check", "bet_33", "bet_75"}
    assert ev["bet_33"] > ev["check"]


def test_strategy_tree_returns_facing_bet_action_evs():
    ev = evaluate_actions(
        _normalized_state_facing_bet(),
        hand_class="top_pair_top_kicker",
        board_tags=["k_high", "rainbow", "dry"],
    )

    assert set(ev) == {"fold", "call", "raise_3x"}
    assert ev["fold"] == 0.0


def test_strategy_engine_analyzes_hand_with_normalized_strategy_result():
    from app.engine.analyze_hand import StrategyEngine

    state = replace(_normalized_state(), hero_seat=None)

    result = StrategyEngine().analyze_hand(state)

    assert isinstance(result, AnalysisResult)
    assert result.recommend == "bet_33"
    assert result.recommend == max(result.ev, key=result.ev.get)
    assert result.strategy["bet_33"] > result.strategy["check"]
    assert result.ev["bet_33"] > result.ev["check"]
    assert set(result.strategy) == set(result.ev)
    assert abs(sum(result.strategy.values()) - 1.0) < 0.0001
    assert result.confidence == 0.65
    assert "top_pair_top_kicker" in result.reason_codes
    assert "dry" in result.reason_codes
    assert result.engine_version == ENGINE_VERSION


def test_strategy_engine_analyzes_facing_bet_state():
    from app.engine.analyze_hand import StrategyEngine

    result = StrategyEngine().analyze_hand(_normalized_state_facing_bet())

    assert set(result.ev) == {"fold", "call", "raise_3x"}
    assert result.recommend == "call"
    assert result.recommend == max(result.ev, key=result.ev.get)
    assert abs(sum(result.strategy.values()) - 1.0) < 0.0001


def test_strategy_engine_rejects_non_team_actor_snapshot():
    from app.engine.analyze_hand import StrategyEngine, UnsupportedStateError

    state = replace(_normalized_state(), current_actor="villain")

    with pytest.raises(UnsupportedStateError, match="current actor"):
        StrategyEngine().analyze_hand(state)


@pytest.mark.parametrize(
    "patch, expected_message",
    [
        ({"mode": "team"}, "mode"),
        ({"table_size": 6}, "table size"),
        ({"street": "turn"}, "street"),
        ({"position": "CO_vs_BB"}, "position"),
        ({"board": ["Kc", "8d"]}, "board"),
        ({"known_hands": {"hero": ["Ah"]}}, "hand"),
    ],
)
def test_strategy_engine_rejects_unsupported_v01_state(patch, expected_message):
    from app.engine.analyze_hand import StrategyEngine, UnsupportedStateError

    state = replace(_normalized_state(), **patch)

    with pytest.raises(UnsupportedStateError, match=expected_message):
        StrategyEngine().analyze_hand(state)
