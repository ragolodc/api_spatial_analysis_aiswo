from uuid import UUID

from src.modules.pivot_geometry_analysis.domain.entities import (
    LongitudinalSlopeAnalysis,
    NodeKind,
    NodeStressResult,
    RunKind,
    SpanSlopeResult,
    StressRunResult,
    StructuralStressAnalysis,
)
from src.modules.pivot_geometry_analysis.domain.value_objects import SlopeValue, ThresholdConfig


class ComputeStructuralStress:
    def execute(
        self, request_id: UUID, longitudinal: LongitudinalSlopeAnalysis, config: ThresholdConfig
    ) -> StructuralStressAnalysis:

        nodes = []
        runs = []
        # --- nodes ---
        spans_by_azimuth: dict[float, list[SpanSlopeResult]] = {}
        for span in longitudinal.spans:
            spans_by_azimuth.setdefault(span.azimuth_deg, []).append(span)

        for azimuth, spans in spans_by_azimuth.items():
            spans = sorted(spans, key=lambda s: s.span_index)

            for i in range(len(spans) - 1):
                span_in = spans[i]
                span_out = spans[i + 1]

                delta_pct = span_out.slope.pct - span_in.slope.pct

                if delta_pct > 0:
                    kind = NodeKind.VALLEY
                elif delta_pct < 0:
                    kind = NodeKind.CREST
                else:
                    kind = NodeKind.NEUTRAL

                delta = SlopeValue.from_pct(delta_pct)
                classification = config.classify(delta_pct)
                valley_double_check = (
                    kind == NodeKind.VALLEY and abs(delta_pct) > 2 * config.max_value
                )

                nodes.append(
                    NodeStressResult(
                        azimuth_deg=azimuth,
                        tower_index=i + 1,
                        radius_m=span_in.radius_end_m,
                        slope_in=span_in.slope,
                        slope_out=span_out.slope,
                        delta=delta,
                        node_kind=kind,
                        classification=classification,
                        valley_double_check=valley_double_check,
                    )
                )

            # --- runs ---
            current_run: list[SpanSlopeResult] = []
            for span in spans:
                if not current_run or (span.slope.pct * current_run[-1].slope.pct > 0):
                    current_run.append(span)
                else:
                    if len(current_run) >= 2:
                        kind_run = (
                            RunKind.TENSION if current_run[0].slope.pct < 0 else RunKind.COMPRESSION
                        )
                        runs.append(
                            StressRunResult(
                                azimuth_deg=azimuth,
                                run_kind=kind_run,
                                span_indices=[s.span_index for s in current_run],
                                cumulative_slope_pct=sum(s.slope.pct for s in current_run),
                            )
                        )
                    current_run = [span]
            if len(current_run) >= 2:
                kind_run = RunKind.TENSION if current_run[0].slope.pct < 0 else RunKind.COMPRESSION
                runs.append(
                    StressRunResult(
                        azimuth_deg=azimuth,
                        run_kind=kind_run,
                        span_indices=[s.span_index for s in current_run],
                        cumulative_slope_pct=sum(s.slope.pct for s in current_run),
                    )
                )

        return StructuralStressAnalysis(request_id=request_id, nodes=nodes, runs=runs)
