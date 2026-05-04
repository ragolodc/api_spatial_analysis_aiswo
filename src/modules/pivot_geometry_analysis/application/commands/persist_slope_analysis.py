from src.modules.pivot_geometry_analysis.domain.entities import (
    SlopeAnalysisJobRequest,
    SlopeAnalysisResult,
)
from src.modules.pivot_geometry_analysis.domain.ports import SlopeAnalysisResultWriter


class PersistSlopeAnalysis:
    """Application command to persist  slope analysis samples into analytical storage."""

    def __init__(self, warehouse: SlopeAnalysisResultWriter) -> None:
        self._warehouse = warehouse

    def execute(self, result: SlopeAnalysisResult, job_request: SlopeAnalysisJobRequest) -> None:
        self._warehouse.store_result(result, job_request)
