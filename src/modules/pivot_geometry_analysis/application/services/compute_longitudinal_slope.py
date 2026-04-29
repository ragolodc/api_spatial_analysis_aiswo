from uuid import UUID

from src.modules.pivot_geometry_analysis.domain.entities import (
    LongitudinalSlopeAnalysis,
    SpanSlopeResult,
)
from src.modules.pivot_geometry_analysis.domain.value_objects import SlopeValue, ThresholdConfig
from src.modules.profile_analysis.domain.entities import LongitudinalProfile, SpansConfig


class ComputeLongitudinalSlope:
    def execute(
        self,
        request_id: UUID,
        profiles: list[LongitudinalProfile],
        spans_config: SpansConfig,
        config: ThresholdConfig,
    ) -> LongitudinalSlopeAnalysis:
        spans: list[SpanSlopeResult] = []
        for _, profile in enumerate(profiles):
            points_by_radius = {p.radius_m: p for p in profile.points}
            radii_m = spans_config.get_radii_m()
            tower_radii = (0.0, *radii_m)
            for i in range(len(tower_radii) - 1):
                r_start = tower_radii[i]
                r_end = tower_radii[i + 1]

                span = spans_config.get_span_by_position(i + 1)

                p_start = points_by_radius.get(r_start)
                p_end = points_by_radius.get(r_end)

                if p_start is None or p_end is None:
                    raise ValueError(
                        f"Missing point at radius {r_start} or {r_end} in \
                              profile {profile.azimuth_deg}º"
                    )

                if p_start.elevation_m is None or p_end.elevation_m is None:
                    continue

                dz = p_end.elevation_m - p_start.elevation_m
                dx = p_end.radius_m - p_start.radius_m

                slope = SlopeValue.from_ratio(dz=dz, dx=dx)

                classification = config.classify(slope.pct)

                spans.append(
                    SpanSlopeResult(
                        azimuth_deg=profile.azimuth_deg,
                        span_index=i,
                        radius_start_m=r_start,
                        radius_end_m=r_end,
                        slope=slope,
                        classification=classification,
                        service_weight=span.service_weight,
                    )
                )

        return LongitudinalSlopeAnalysis(request_id=request_id, spans=spans)
