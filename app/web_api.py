from dataclasses import asdict
from typing import Any

from app.collector.sample_website_states import get_sample_website_state
from app.collector.website_state import (
    CollectedStateError,
    convert_website_state_to_raw_state,
)
from app.engine.analyze_hand import StrategyEngine
from app.schema.result import AnalysisResult
from app.services.analysis_service import normalize_raw_state


def analyze_raw_payload(payload: Any) -> dict:
    if not isinstance(payload, dict):
        return {"ok": False, "error": "INVALID_PAYLOAD"}

    try:
        _validate_payload_shape(payload)
        state = normalize_raw_state(payload)
        result = StrategyEngine().analyze_hand(state)
    except (KeyError, TypeError, ValueError) as exc:
        return {"ok": False, "error": _error_message(exc)}

    return {"ok": True, "result": serialize_analysis_result(result)}


def load_collected_state_payload(scenario: str) -> dict:
    try:
        collected_state = get_sample_website_state(scenario)
        raw_state = convert_website_state_to_raw_state(collected_state)
    except CollectedStateError as exc:
        return {"ok": False, "error": str(exc)}

    return {
        "ok": True,
        "collected_state": collected_state,
        "raw_state": raw_state,
    }


def import_website_state_payload(payload: Any) -> dict:
    if not isinstance(payload, dict):
        return {"ok": False, "error": "INVALID_PAYLOAD"}

    try:
        raw_state = convert_website_state_to_raw_state(payload)
    except CollectedStateError as exc:
        return {"ok": False, "error": str(exc)}

    return {
        "ok": True,
        "collected_state": payload,
        "raw_state": raw_state,
    }


def _validate_payload_shape(payload: dict) -> None:
    for field in ("known_hands", "effective_stacks"):
        if field in payload and not isinstance(payload[field], dict):
            raise TypeError(f"INVALID_FIELD: {field}")


def serialize_analysis_result(result: AnalysisResult) -> dict:
    return asdict(result)


def _error_message(exc: Exception) -> str:
    if isinstance(exc, KeyError):
        return f"MISSING_FIELD: {exc.args[0]}"
    message = str(exc)
    return message if message else exc.__class__.__name__
