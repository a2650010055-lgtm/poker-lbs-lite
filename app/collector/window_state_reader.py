from collections.abc import Callable

from app.collector.base import RawCollectedState, StateReader


class WindowStateReader(StateReader):
    def __init__(self, state_provider: Callable[[], RawCollectedState]):
        self._state_provider = state_provider

    def read_raw_state(self) -> RawCollectedState:
        state = self._state_provider()
        if not isinstance(state, dict):
            raise ValueError("COLLECTOR_FAILED")
        return state
