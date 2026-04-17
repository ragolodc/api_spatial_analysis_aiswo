from uuid import uuid4

from src.modules.profile_analysis.application.commands import (
    PersistProfileAnalysisJob,
    QueueProfileAnalysis,
)
from src.modules.profile_analysis.domain.entities import ProfileAnalysisJobStatus


class FakeJobRepository:
    def __init__(self) -> None:
        self.items = {}

    def save(self, job):
        self.items[job.request_id] = job
        return job

    def find_by_id(self, request_id):
        return self.items.get(request_id)

    def update(self, job):
        self.items[job.request_id] = job
        return job


class FakeDispatcher:
    def __init__(self) -> None:
        self.dispatched = []

    def dispatch(self, request):
        self.dispatched.append(request)


def test_queue_profile_analysis_persists_queued_job_and_dispatches() -> None:
    repo = FakeJobRepository()
    dispatcher = FakeDispatcher()
    persist_job = PersistProfileAnalysisJob(repo)

    request_id = QueueProfileAnalysis(dispatcher=dispatcher, persist_job=persist_job).execute(
        zone_id=uuid4(),
        payload={"inputs": {"pivot_kind": "circular", "center": [0.0, 0.0], "radii_m": [10.0]}},
    )

    assert request_id in repo.items
    assert repo.items[request_id].status == ProfileAnalysisJobStatus.QUEUED
    assert len(dispatcher.dispatched) == 1
    assert dispatcher.dispatched[0].request_id == request_id


def test_persist_profile_analysis_job_marks_lifecycle_transitions() -> None:
    repo = FakeJobRepository()
    service = PersistProfileAnalysisJob(repo)
    request_id = uuid4()
    zone_id = uuid4()

    queued = service.queue(request_id=request_id, zone_id=zone_id, payload={"inputs": {}})
    running = service.mark_running(request_id)
    completed = service.mark_completed(request_id, result_payload={"total_points": 10})

    assert queued.status == ProfileAnalysisJobStatus.QUEUED
    assert running.status == ProfileAnalysisJobStatus.RUNNING
    assert completed.status == ProfileAnalysisJobStatus.COMPLETED
    assert completed.result_payload == {"total_points": 10}
