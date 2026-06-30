from app.config import ENGINE_VERSION
from app.engine.board_texture import classify_board
from app.engine.hand_evaluator import classify_made_hand
from app.engine.strategy_tree import evaluate_actions
from app.schema.actions import ALL_IN
from app.schema.result import AnalysisResult
from app.schema.state import NormalizedState


class UnsupportedStateError(ValueError):
    pass


class StrategyEngine:
    def analyze_hand(self, state: NormalizedState) -> AnalysisResult:
        _validate_supported_state(state)
        actor_hand = state.known_hands[state.current_actor]
        hand_class = classify_made_hand(actor_hand, state.board)
        board_tags = classify_board(state.board)
        ev = evaluate_actions(state, hand_class, board_tags)
        recommend = max(ev, key=ev.get)
        strategy = _normalize_positive_ev(ev)
        return AnalysisResult(
            recommend=recommend,
            strategy=strategy,
            ev=ev,
            confidence=0.65,
            reason_codes=[hand_class, *board_tags],
            engine_version=ENGINE_VERSION,
        )


def _normalize_positive_ev(ev: dict[str, float]) -> dict[str, float]:
    positive_ev = {action: max(value, 0.0) for action, value in ev.items()}
    total = sum(positive_ev.values())
    if total <= 0:
        share = 1.0 / len(positive_ev)
        return {action: share for action in positive_ev}
    return {action: value / total for action, value in positive_ev.items()}


def _validate_supported_state(state: NormalizedState) -> None:
    if state.mode != "single":
        raise UnsupportedStateError("unsupported mode for V0.1 strategy engine")
    if state.table_size != 2:
        raise UnsupportedStateError("unsupported table size for V0.1 strategy engine")
    if state.street != "flop":
        raise UnsupportedStateError("unsupported street for V0.1 strategy engine")
    if state.position != "BTN_vs_BB":
        raise UnsupportedStateError("unsupported position for V0.1 strategy engine")
    if state.objective != "actor_ev":
        raise UnsupportedStateError("unsupported objective for V0.1 strategy engine")
    if len(state.board) != 3:
        raise UnsupportedStateError("board must contain exactly 3 flop cards")
    if any(action.get("action") == ALL_IN for action in state.action_history):
        raise UnsupportedStateError("all-in action is unsupported in V0.1")
    if (
        state.current_actor != state.hero_seat
        and state.current_actor not in state.team_seats
    ):
        raise UnsupportedStateError("current actor must be the hero/team actor")
    if state.current_actor not in state.known_hands:
        raise UnsupportedStateError("current actor hand must be known")
    if len(state.known_hands[state.current_actor]) != 2:
        raise UnsupportedStateError("current actor hand must contain exactly 2 cards")
