from app.collector.state_hash import build_state_hash
from app.collector.base import StateReader
from app.engine.analyze_hand import StrategyEngine
from app.schema.cards import validate_unique_cards
from app.schema.result import AnalysisResult
from app.schema.state import NormalizedState


def normalize_raw_state(raw: dict) -> NormalizedState:
    known_hands = {
        seat: list(hand) for seat, hand in raw.get("known_hands", {}).items()
    }
    board = list(raw.get("board", []))
    all_cards: list[str] = []
    for hand in known_hands.values():
        all_cards.extend(hand)
    all_cards.extend(board)
    validate_unique_cards(all_cards)

    hero_seat = raw.get("hero_seat")
    team_seats = (
        list(raw["team_seats"])
        if raw.get("team_seats")
        else ([hero_seat] if hero_seat else [])
    )
    unknown_seats = list(raw.get("unknown_seats", []))
    effective_stacks = {
        seat: float(stack) for seat, stack in raw.get("effective_stacks", {}).items()
    }
    action_history = [dict(action) for action in raw.get("action_history", [])]
    normalized_source = {
        "mode": raw.get("mode", "single"),
        "table_size": int(raw["table_size"]),
        "street": raw["street"],
        "position": raw["position"],
        "current_actor": raw["current_actor"],
        "hero_seat": hero_seat,
        "team_seats": team_seats,
        "known_hands": known_hands,
        "unknown_seats": unknown_seats,
        "board": board,
        "pot": float(raw["pot"]),
        "effective_stacks": effective_stacks,
        "action_history": action_history,
        "objective": raw.get("objective", "actor_ev"),
    }
    return NormalizedState(
        **normalized_source,
        state_hash=build_state_hash(normalized_source),
    )


def analyze_collected_state(reader: StateReader) -> AnalysisResult:
    raw = reader.read_raw_state()
    state = normalize_raw_state(raw)
    return StrategyEngine().analyze_hand(state)
