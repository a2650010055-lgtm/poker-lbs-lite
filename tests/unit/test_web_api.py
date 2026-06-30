import json
from pathlib import Path

from app.web_api import analyze_raw_payload


FIXTURE_DIR = Path(__file__).parents[1] / "fixtures"


def load_fixture(name: str) -> dict:
    return json.loads((FIXTURE_DIR / name).read_text(encoding="utf-8"))


def test_analyze_raw_payload_returns_success_for_check_spot():
    response = analyze_raw_payload(load_fixture("flop_btn_bb_unopened.json"))

    assert response["ok"] is True
    result = response["result"]
    assert result["recommend"] in result["strategy"]
    assert set(result["strategy"]) == {"check", "bet_33", "bet_75"}
    assert set(result["ev"]) == {"check", "bet_33", "bet_75"}
    assert result["engine_version"] == "lbs-lite-0.1.0"


def test_analyze_raw_payload_returns_facing_bet_actions():
    response = analyze_raw_payload(load_fixture("flop_btn_bb_facing_bet.json"))

    assert response["ok"] is True
    result = response["result"]
    assert result["recommend"] in result["strategy"]
    assert set(result["strategy"]) == {"fold", "call", "raise_3x"}
    assert set(result["ev"]) == {"fold", "call", "raise_3x"}


def test_analyze_raw_payload_returns_duplicate_card_error():
    raw = load_fixture("flop_btn_bb_unopened.json")
    raw["board"][0] = "Ah"

    response = analyze_raw_payload(raw)

    assert response == {"ok": False, "error": "DUPLICATE_CARD"}


def test_analyze_raw_payload_returns_unsupported_state_error():
    raw = load_fixture("flop_btn_bb_unopened.json")
    raw["street"] = "turn"
    raw["board"] = ["Kc", "8d", "3s", "2c"]

    response = analyze_raw_payload(raw)

    assert response["ok"] is False
    assert "unsupported street" in response["error"]


def test_analyze_raw_payload_rejects_non_dict_payload():
    response = analyze_raw_payload(["not", "a", "state"])

    assert response == {"ok": False, "error": "INVALID_PAYLOAD"}
