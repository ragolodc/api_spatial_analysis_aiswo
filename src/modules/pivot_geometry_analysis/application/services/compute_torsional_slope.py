from uuid import UUID

from src.modules.pivot_geometry_analysis.domain.entities import (
    LongitudinalSlopeAnalysis,
    SpanSlopeResult,
    TorsionalSlopeAnalysis,
    TorsionalSlopeResult,
    TransversalSlopeAnalysis,
    TransversalSlopePoint,
)
from src.modules.pivot_geometry_analysis.domain.value_objects import SlopeValue, ThresholdConfig


class ComputeTorsionalSlope:
    def execute(
        self,
        request_id: UUID,
        longitudinal: LongitudinalSlopeAnalysis,
        transversal: TransversalSlopeAnalysis,
        torsion_config: ThresholdConfig,
        longitudinal_config: ThresholdConfig,
    ) -> TorsionalSlopeAnalysis:

        transversal_index: dict[float, list[TransversalSlopePoint]] = {}

        for pt in transversal.points:
            transversal_index.setdefault(pt.radius_m, []).append(pt)

        def find_transversal(radius_m: float, azimuth_deg: float) -> SlopeValue | None:
            candidates = transversal_index.get(radius_m, [])
            for pt in candidates:
                if pt.azimuth_from_deg <= azimuth_deg <= pt.azimuth_to_deg:
                    return pt.slope
            return None

        spans_by_azimuth: dict[float, list[SpanSlopeResult]] = {}

        for span in longitudinal.spans:
            spans_by_azimuth.setdefault(span.azimuth_deg, []).append(span)

        result = []

        for azimuth, spans in spans_by_azimuth.items():
            for span in sorted(spans, key=lambda s: s.span_index):
                alpha_inner = find_transversal(radius_m=span.radius_start_m, azimuth_deg=azimuth)
                alpha_outer = find_transversal(radius_m=span.radius_end_m, azimuth_deg=azimuth)

                if alpha_inner is None or alpha_outer is None:
                    continue

                torsion_pct = alpha_outer.pct - alpha_inner.pct
                torsion = SlopeValue.from_pct(torsion_pct)

                combined = (
                    abs(torsion_pct) / torsion_config.max_value
                    + abs(span.slope.pct) / longitudinal_config.max_value
                )

                classification = torsion_config.classify(torsion.pct)

                result.append(
                    TorsionalSlopeResult(
                        azimuth_deg=azimuth,
                        span_index=span.span_index,
                        radius_start_m=span.radius_start_m,
                        radius_end_m=span.radius_end_m,
                        alpha_inner=alpha_inner,
                        alpha_outer=alpha_outer,
                        torsion=torsion,
                        longitudinal_slope=span.slope,
                        combined_load_index=combined,
                        classification=classification,
                    )
                )
        return TorsionalSlopeAnalysis(request_id=request_id, spans=result)
