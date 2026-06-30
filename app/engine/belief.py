from app.engine.ranges import BTN_VS_BB_CALL_RANGE
from app.schema.state import NormalizedState


class BeliefModel:
    def estimate_ranges(self, state: NormalizedState) -> dict[str, dict[str, float]]:
        return {seat: self._range_for_seat(state, seat) for seat in state.unknown_seats}

    def _range_for_seat(self, state: NormalizedState, seat: str) -> dict[str, float]:
        if state.position == "BTN_vs_BB":
            return dict(BTN_VS_BB_CALL_RANGE)
        return {}
