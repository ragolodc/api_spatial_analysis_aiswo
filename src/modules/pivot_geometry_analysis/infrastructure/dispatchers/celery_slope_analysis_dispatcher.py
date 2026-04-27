from src.modules.pivot_geometry_analysis.domain.entities import SlopeAnalysisJobRequest
from src.modules.pivot_geometry_analysis.domain.ports import SlopeAnalysisJobDispatcher
from src.shared.workers.celery_app import celery_app

_TASK_NAME = "src.shared.workers.tasks.slope_analysis_tasks.generate_slope_analysis"


class CelerySlopeAnalysisDispatcher(SlopeAnalysisJobDispatcher):
    """Infrastructure adapter that sends slope jobs to Celery."""

    def dispatch(self, request: SlopeAnalysisJobRequest) -> None:
        celery_app.send_task(
            _TASK_NAME,
            kwargs={
                "request_id": str(request.request_id),
                "zone_id": str(request.zone_id),
                "profile_analysis_id": str(request.profile_analysis_id),
                "payload": request.payload,
            },
        )
