from dataclasses import dataclass


@dataclass(frozen=True)
class AnalysisResult:
    recommend: str
    strategy: dict[str, float]
    ev: dict[str, float]
    confidence: float
    reason_codes: list[str]
    engine_version: str
    solver_reference: dict | None = None
