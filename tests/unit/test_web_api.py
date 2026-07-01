import json
from pathlib import Path

from app.web_api import (
    analyze_raw_payload,
    import_website_state_payload,
    load_collected_state_payload,
)


FIXTURE_DIR = Path(__file__).parents[1] / "fixtures"


def load_fixture(name: str) -> dict:
    return json.loads((FIXTURE_DIR / name).read_text(encoding="utf-8"))


def make_website_state() -> dict:
    return {
        "table_id": "real-table-1",
        "hand_id": "real-hand-001",
        "street": "flop",
        "position": "BTN_vs_BB",
        "current_actor": "hero",
        "hero_cards": ["Ah", "Kh"],
        "board_cards": ["Kc", "8d", "3s"],
        "pot": 100,
        "stacks": {
            "hero": 900,
            "villain": 900,
        },
        "facing_action": {
            "player": "BB",
            "action": "check",
            "size": 0,
        },
    }


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


def test_analyze_raw_payload_returns_error_for_malformed_field_shape():
    raw = load_fixture("flop_btn_bb_unopened.json")
    raw["known_hands"] = []

    response = analyze_raw_payload(raw)

    assert response["ok"] is False
    assert response["error"]


def test_load_collected_state_payload_returns_converted_check_state():
    response = load_collected_state_payload("check")

    assert response["ok"] is True
    assert response["collected_state"]["hand_id"] == "demo-check-001"
    assert response["raw_state"]["known_hands"] == {"hero": ["Ah", "Kh"]}
    assert response["raw_state"]["action_history"] == [
        {"player": "BB", "action": "check"}
    ]


def test_load_collected_state_payload_returns_error_for_unknown_scenario():
    response = load_collected_state_payload("unknown")

    assert response == {
        "ok": False,
        "error": "UNSUPPORTED_COLLECTED_SCENARIO",
    }


def test_import_website_state_payload_returns_converted_raw_state():
    response = import_website_state_payload(make_website_state())

    assert response["ok"] is True
    assert response["collected_state"]["hand_id"] == "real-hand-001"
    assert response["raw_state"]["known_hands"] == {"hero": ["Ah", "Kh"]}
    assert response["raw_state"]["board"] == ["Kc", "8d", "3s"]
    assert response["raw_state"]["action_history"] == [
        {"player": "BB", "action": "check"}
    ]


def test_import_website_state_payload_rejects_non_dict_payload():
    response = import_website_state_payload(["not", "a", "state"])

    assert response == {"ok": False, "error": "INVALID_PAYLOAD"}


def test_import_website_state_payload_returns_collected_state_error():
    payload = make_website_state()
    del payload["hero_cards"]

    response = import_website_state_payload(payload)

    assert response["ok"] is False
    assert response["error"].startswith("INVALID_COLLECTED_STATE:")
    assert "hero_cards" in response["error"]
