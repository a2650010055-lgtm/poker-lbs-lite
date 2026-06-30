from app.collector.state_hash import build_state_hash


def test_state_hash_stable_for_same_state_with_different_key_order():
    left = {"street": "flop", "pot": 100, "board": ["Kc", "8d", "3s"]}
    right = {"board": ["Kc", "8d", "3s"], "pot": 100, "street": "flop"}
    assert build_state_hash(left) == build_state_hash(right)


def test_state_hash_changes_when_action_changes():
    left = {"street": "flop", "action_history": [{"action": "check"}]}
    right = {"street": "flop", "action_history": [{"action": "bet", "size": 33}]}
    assert build_state_hash(left) != build_state_hash(right)
