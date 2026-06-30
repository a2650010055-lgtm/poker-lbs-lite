from abc import ABC, abstractmethod
from typing import Any, TypedDict


class RawCollectedState(TypedDict):
    mode: str
    table_size: int
    street: str
    position: str
    current_actor: str
    hero_seat: str | None
    known_hands: dict[str, list[str]]
    unknown_seats: list[str]
    board: list[str]
    pot: float | int
    effective_stacks: dict[str, float | int]
    action_history: list[dict[str, Any]]
    objective: str


class StateReader(ABC):
    @abstractmethod
    def read_raw_state(self) -> RawCollectedState:
        raise NotImplementedError
