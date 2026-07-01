from typing import Any, TypeAlias

from app.collector.base import RawCollectedState


WebsiteState: TypeAlias = dict[str, Any]


class CollectedStateError(ValueError):
    pass


REQUIRED_FIELDS = (
    "street",
    "position",
    "current_actor",
    "hero_cards",
    "board_cards",
    "pot",
    "stacks",
    "facing_action",
)


def convert_website_state_to_raw_state(state: WebsiteState) -> RawCollectedState:
    if not isinstance(state, dict):
        raise CollectedStateError("INVALID_COLLECTED_STATE: root")

    for field in REQUIRED_FIELDS:
        if field not in state:
            raise CollectedStateError(f"INVALID_COLLECTED_STATE: {field}")

    _require_value(state, "street", "flop")
    _require_value(state, "position", "BTN_vs_BB")
    _require_value(state, "current_actor", "hero")

    hero_cards = _require_card_list(state, "hero_cards", 2)
    board_cards = _require_card_list(state, "board_cards", 3)
    pot = _require_number(state, "pot")
    stacks = _require_mapping(state, "stacks")
    hero_stack = _require_number(stacks, "hero", "stacks.hero")
    villain_stack = _require_number(stacks, "villain", "stacks.villain")
    facing_action = _require_mapping(state, "facing_action")

    return {
        "mode": "single",
        "table_size": 2,
        "street": "flop",
        "position": "BTN_vs_BB",
        "current_actor": "hero",
        "hero_seat": "hero",
        "known_hands": {"hero": hero_cards},
        "unknown_seats": ["villain"],
        "board": board_cards,
        "pot": pot,
        "effective_stacks": {"hero": hero_stack, "villain": villain_stack},
        "action_history": [_convert_facing_action(facing_action)],
        "objective": "actor_ev",
    }


def _require_value(state: WebsiteState, key: str, expected: str) -> None:
    if state.get(key) != expected:
        raise CollectedStateError(f"UNSUPPORTED_COLLECTED_STATE: {key}")


def _require_mapping(
    state: dict[str, Any],
    key: str,
    error_key: str | None = None,
) -> dict[str, Any]:
    value = state.get(key)
    if not isinstance(value, dict):
        raise CollectedStateError(f"INVALID_COLLECTED_STATE: {error_key or key}")
    return value


def _require_card_list(state: WebsiteState, key: str, length: int) -> list[str]:
    value = state.get(key)
    if (
        not isinstance(value, list)
        or len(value) != length
        or any(not isinstance(card, str) or not card for card in value)
    ):
        raise CollectedStateError(f"INVALID_COLLECTED_STATE: {key}")
    return list(value)


def _require_number(
    state: dict[str, Any],
    key: str,
    error_key: str | None = None,
) -> int | float:
    value = state.get(key)
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise CollectedStateError(f"INVALID_COLLECTED_STATE: {error_key or key}")
    return value


def _convert_facing_action(action: dict[str, Any]) -> dict[str, Any]:
    player = action.get("player")
    if player != "BB":
        raise CollectedStateError("UNSUPPORTED_COLLECTED_STATE: facing_action.player")

    action_name = action.get("action")
    if action_name == "check":
        return {"player": "BB", "action": "check"}

    if action_name == "bet":
        size = _require_number(action, "size", "facing_action.size")
        if size <= 0:
            raise CollectedStateError("INVALID_COLLECTED_STATE: facing_action.size")
        return {"player": "BB", "action": "bet", "size": size}

    raise CollectedStateError("UNSUPPORTED_COLLECTED_STATE: facing_action.action")
