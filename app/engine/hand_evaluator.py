RANK_ORDER = "23456789TJQKA"


def classify_made_hand(hero_hand: list[str], board: list[str]) -> str:
    hero_ranks = [card[0] for card in hero_hand]
    board_ranks = [card[0] for card in board]
    top_board_rank = max(board_ranks, key=RANK_ORDER.index)
    pairs_top_board_rank = top_board_rank in hero_ranks
    if pairs_top_board_rank and top_board_rank == "A" and "K" in hero_ranks:
        return "top_pair_top_kicker"
    if pairs_top_board_rank and top_board_rank != "A" and "A" in hero_ranks:
        return "top_pair_top_kicker"
    if len(set(hero_ranks)) < len(hero_ranks) or any(rank in board_ranks for rank in hero_ranks):
        return "pair"
    return "high_card"
