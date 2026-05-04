from dataclasses import dataclass
from datetime import datetime, timezone
from uuid import uuid4

from src.modules.pivot_geometry_analysis.application.queries import GetSlopeAnalysisResults
from src.modules.pivot_geometry_analysis.domain.entities import (
    SlopeAnalysisJob,
    SlopeAnalysisJobStatus,
)


@dataclass
class _RepoStub:
    job: SlopeAnalysisJob | None

    def find_by_id(self, request_id):  # pragma: no cover - simple stub
        return self.job


@dataclass
class _ReaderStub:
    payload: dict | None

    def get_result_payload(self, request_id):  # pragma: no cover - simple stub
        return self.payload


def _completed_job(result_payload: dict | None) -> SlopeAnalysisJob:
    request_id = uuid4()
    return SlopeAnalysisJob(
        request_id=request_id,
        zone_id=uuid4(),
        profile_analysis_id=uuid4(),
        status=SlopeAnalysisJobStatus.COMPLETED,
        payload={"inputs": {}},
        result_payload=result_payload,
        error_message=None,
        queued_at=datetime.now(timezone.utc),
        started_at=None,
        completed_at=datetime.now(timezone.utc),
    )


def test_returns_detailed_payload_from_reader_when_available():
    detailed_payload = {
        "request_id": str(uuid4()),
        "longitudinal_slope_analysis": {"request_id": "x", "spans": []},
    }
    legacy_payload = {
        "request_id": str(uuid4()),
        "longitudinal_slope_analysis": str(uuid4()),
    }

    use_case = GetSlopeAnalysisResults(
        repository=_RepoStub(job=_completed_job(legacy_payload)),
        result_reader=_ReaderStub(payload=detailed_payload),
    )

    result = use_case.execute(uuid4())

    assert result == detailed_payload


def test_returns_none_when_reader_has_no_data_even_if_job_has_legacy_payload():
    legacy_payload = {
        "request_id": str(uuid4()),
        "longitudinal_slope_analysis": str(uuid4()),
    }

    use_case = GetSlopeAnalysisResults(
        repository=_RepoStub(job=_completed_job(legacy_payload)),
        result_reader=_ReaderStub(payload=None),
    )

    result = use_case.execute(uuid4())

    assert result is None


def test_returns_none_when_job_is_not_completed():
    request_id = uuid4()
    job = SlopeAnalysisJob(
        request_id=request_id,
        zone_id=uuid4(),
        profile_analysis_id=uuid4(),
        status=SlopeAnalysisJobStatus.RUNNING,
        payload={"inputs": {}},
        result_payload=None,
        error_message=None,
        queued_at=datetime.now(timezone.utc),
        started_at=datetime.now(timezone.utc),
        completed_at=None,
    )

    use_case = GetSlopeAnalysisResults(
        repository=_RepoStub(job=job),
        result_reader=_ReaderStub(payload={"unexpected": True}),
    )

    result = use_case.execute(request_id)

    assert result is None
