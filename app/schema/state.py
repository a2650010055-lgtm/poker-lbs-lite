from dataclasses import dataclass, field


@dataclass(frozen=True)
class NormalizedState:
    mode: str
    table_size: int
    street: str
    position: str
    current_actor: str
    hero_seat: str | None
    team_seats: list[str]
    known_hands: dict[str, list[str]]
    unknown_seats: list[str]
    board: list[str]
    pot: float
    effective_stacks: dict[str, float]
    action_history: list[dict]
    objective: str
    state_hash: str = field(default="")
