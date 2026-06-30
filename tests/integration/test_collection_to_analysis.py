import json
from pathlib import Path

import pytest

from app.collector.window_state_reader import WindowStateReader
from app.engine.analyze_hand import UnsupportedStateError
from app.schema.result import AnalysisResult
from app.services.analysis_service import analyze_collected_state


FIXTURE_DIR = Path(__file__).parents[1] / "fixtures"


def load_fixture(name: str) -> dict:
    return json.loads((FIXTURE_DIR / name).read_text(encoding="utf-8"))


def test_collection_to_analysis_returns_strategy_result():
    reader = WindowStateReader(
        lambda: {
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
    )

    result = analyze_collected_state(reader)

    assert isinstance(result, AnalysisResult)
    assert result.recommend == "bet_33"
    assert result.engine_version == "lbs-lite-0.1.0"


def test_collection_to_analysis_uses_collected_action_history():
    reader = WindowStateReader(
        lambda: {
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
            "action_history": [{"player": "BB", "action": "bet_33"}],
            "objective": "actor_ev",
        }
    )

    result = analyze_collected_state(reader)

    assert set(result.strategy) == {"fold", "call", "raise_3x"}


def test_regression_unopened_flop_fixture():
    reader = WindowStateReader(lambda: load_fixture("flop_btn_bb_unopened.json"))

    result = analyze_collected_state(reader)

    assert result.recommend in result.strategy
    assert set(result.strategy) == {"check", "bet_33", "bet_75"}


def test_regression_facing_bet_fixture():
    reader = WindowStateReader(lambda: load_fixture("flop_btn_bb_facing_bet.json"))

    result = analyze_collected_state(reader)

    assert result.recommend in result.strategy
    assert set(result.strategy) == {"fold", "call", "raise_3x"}


def test_collection_to_analysis_rejects_all_in_for_v01():
    raw = load_fixture("flop_btn_bb_unopened.json")
    raw["action_history"] = [{"player": "BB", "action": "all_in"}]
    reader = WindowStateReader(lambda: raw)

    with pytest.raises(UnsupportedStateError, match="all-in"):
        analyze_collected_state(reader)


def test_collection_to_analysis_rejects_unsupported_objective():
    raw = load_fixture("flop_btn_bb_unopened.json")
    raw["objective"] = "team_ev"
    reader = WindowStateReader(lambda: raw)

    with pytest.raises(UnsupportedStateError, match="objective"):
        analyze_collected_state(reader)
