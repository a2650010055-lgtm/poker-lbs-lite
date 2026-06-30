import hashlib
import json


def build_state_hash(state: dict) -> str:
    payload = json.dumps(state, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()
