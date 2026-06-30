from app.schema.actions import (
    ALL_IN,
    BET_33,
    BET_75,
    RAISE_3X,
    V01_FACING_BET_ACTIONS,
    V01_NO_BET_ACTIONS,
)
from app.schema.state import NormalizedState

AGGRESSIVE_ACTIONS = {"bet", "raise", BET_33, BET_75, RAISE_3X}
UNSUPPORTED_V01_ACTIONS = {ALL_IN}


class ActionGenerator:
    def legal_actions(self, state: NormalizedState) -> list[str]:
        if self._is_facing_bet(state):
            return list(V01_FACING_BET_ACTIONS)
        return list(V01_NO_BET_ACTIONS)

    def _is_facing_bet(self, state: NormalizedState) -> bool:
        if not state.action_history:
            return False
        for history_item in state.action_history:
            action = history_item.get("action")
            if action in UNSUPPORTED_V01_ACTIONS:
                raise ValueError(f"UNSUPPORTED_ACTION: {action}")
        last = state.action_history[-1]
        action = last.get("action")
        return (
            last.get("player") != state.current_actor
            and action in AGGRESSIVE_ACTIONS
        )
