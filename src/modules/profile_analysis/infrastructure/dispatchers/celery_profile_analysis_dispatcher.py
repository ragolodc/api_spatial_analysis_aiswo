from src.modules.profile_analysis.domain.entities import ProfileAnalysisJobRequest
from src.modules.profile_analysis.domain.ports import ProfileAnalysisJobDispatcher
from src.shared.workers.celery_app import celery_app

_TASK_NAME = "src.shared.workers.tasks.profile_analysis_tasks.generate_zone_profiles"


class CeleryProfileAnalysisDispatcher(ProfileAnalysisJobDispatcher):
    """Infrastructure adapter that sends profile jobs to Celery."""

    def dispatch(self, request: ProfileAnalysisJobRequest) -> None:
        celery_app.send_task(
            _TASK_NAME,
            kwargs={
                "request_id": str(request.request_id),
                "zone_id": str(request.zone_id),
                "payload": request.payload,
            },
        )
