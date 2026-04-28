from src.modules.pivot_geometry_analysis.domain.entities import (
    SlopeAnalysisJobRequest,
    SlopeAnalysisResult,
)
from src.modules.pivot_geometry_analysis.infrastructure.warehouses.clickhouse_slope_analysis_warehouse import (
    ClickHouseSlopeAnalysisWarehouse,
)


class PersistSlopeAnalysis:
    """Application command to persist  slope analysis samples into analytical storage."""

    def __init__(self, warehouse: ClickHouseSlopeAnalysisWarehouse) -> None:
        self._warehouse = warehouse

    def execute(self, result: SlopeAnalysisResult, job_request: SlopeAnalysisJobRequest) -> None:
        self._warehouse.store_result(result, job_request)
