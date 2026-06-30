from app.schema.actions import BET_33, BET_75, CALL, CHECK, FOLD, RAISE_3X


def estimate_action_ev(
    action: str,
    pot: float,
    hand_class: str,
    board_tags: list[str],
    facing_bet: bool,
) -> float:
    strength = _hand_strength(hand_class)
    dry_bonus = 4.0 if "dry" in board_tags else 0.0
    if action == CHECK:
        return pot * strength * 0.18
    if action == BET_33:
        return pot * strength * 0.24 + dry_bonus
    if action == BET_75:
        return pot * strength * 0.20
    if action == FOLD:
        return 0.0
    if action == CALL:
        return pot * strength * 0.16
    if action == RAISE_3X:
        return pot * strength * 0.18 - 5.0
    return 0.0


def _hand_strength(hand_class: str) -> float:
    if hand_class == "top_pair_top_kicker":
        return 0.78
    if hand_class == "pair":
        return 0.48
    return 0.25
