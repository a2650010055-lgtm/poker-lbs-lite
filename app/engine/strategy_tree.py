from app.engine.action_generator import ActionGenerator
from app.engine.ev import estimate_action_ev
from app.schema.actions import FOLD
from app.schema.state import NormalizedState


def evaluate_actions(
    state: NormalizedState,
    hand_class: str,
    board_tags: list[str],
) -> dict[str, float]:
    actions = ActionGenerator().legal_actions(state)
    facing_bet = FOLD in actions
    return {
        action: estimate_action_ev(action, state.pot, hand_class, board_tags, facing_bet)
        for action in actions
    }
