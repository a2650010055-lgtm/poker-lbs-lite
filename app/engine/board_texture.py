RANK_ORDER = "23456789TJQKA"


def classify_board(board: list[str]) -> list[str]:
    ranks = [card[0] for card in board]
    suits = [card[1] for card in board]
    top = max(ranks, key=RANK_ORDER.index).lower()
    tags = [f"{top}_high"]
    if len(set(suits)) == 3:
        tags.append("rainbow")
    if _is_dry(ranks, suits):
        tags.append("dry")
    else:
        tags.append("wet")
    return tags


def _is_dry(ranks: list[str], suits: list[str]) -> bool:
    rank_indexes = sorted(RANK_ORDER.index(rank) for rank in ranks)
    connected = max(rank_indexes) - min(rank_indexes) <= 4
    two_tone = len(set(suits)) <= 2
    paired = len(set(ranks)) < len(ranks)
    return not connected and not two_tone and not paired
