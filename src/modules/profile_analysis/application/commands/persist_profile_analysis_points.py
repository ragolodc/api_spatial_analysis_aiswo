from src.modules.profile_analysis.domain.entities import ProfileAnalysisResult
from src.modules.profile_analysis.domain.ports import ProfileAnalysisPointWarehouse


class PersistProfileAnalysisPoints:
    """Application command to persist flattened profile-analysis samples into analytical storage."""

    def __init__(self, warehouse: ProfileAnalysisPointWarehouse) -> None:
        self._warehouse = warehouse

    def execute(self, result: ProfileAnalysisResult) -> None:
        self._warehouse.store_result(result)
