from copy import deepcopy

from app.collector.website_state import CollectedStateError, WebsiteState


_SAMPLE_STATES: dict[str, WebsiteState] = {
    "check": {
        "table_id": "demo-table",
        "hand_id": "demo-check-001",
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
    },
    "bet": {
        "table_id": "demo-table",
        "hand_id": "demo-bet-001",
        "street": "flop",
        "position": "BTN_vs_BB",
        "current_actor": "hero",
        "hero_cards": ["Qh", "Jh"],
        "board_cards": ["Kc", "8d", "3s"],
        "pot": 150,
        "stacks": {
            "hero": 850,
            "villain": 850,
        },
        "facing_action": {
            "player": "BB",
            "action": "bet",
            "size": 50,
        },
    },
}


def get_sample_website_state(scenario: str) -> WebsiteState:
    if scenario not in _SAMPLE_STATES:
        raise CollectedStateError("UNSUPPORTED_COLLECTED_SCENARIO")
    return deepcopy(_SAMPLE_STATES[scenario])
