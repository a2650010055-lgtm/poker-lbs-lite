from dataclasses import asdict
from typing import Any

from app.engine.analyze_hand import StrategyEngine
from app.schema.result import AnalysisResult
from app.services.analysis_service import normalize_raw_state


def analyze_raw_payload(payload: Any) -> dict:
    if not isinstance(payload, dict):
        return {"ok": False, "error": "INVALID_PAYLOAD"}

    try:
        state = normalize_raw_state(payload)
        result = StrategyEngine().analyze_hand(state)
    except (KeyError, TypeError, ValueError) as exc:
        return {"ok": False, "error": _error_message(exc)}

    return {"ok": True, "result": serialize_analysis_result(result)}


def serialize_analysis_result(result: AnalysisResult) -> dict:
    return asdict(result)


def _error_message(exc: Exception) -> str:
    if isinstance(exc, KeyError):
        return f"MISSING_FIELD: {exc.args[0]}"
    message = str(exc)
    return message if message else exc.__class__.__name__
