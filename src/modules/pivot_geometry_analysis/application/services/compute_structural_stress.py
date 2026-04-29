import logging
import math
from typing import Dict, List
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
from src.modules.pivot_geometry_analysis.domain.value_objects import (
    SlopeValue,
    ThresholdConfig,
)

logger = logging.getLogger(__name__)


class ComputeStructuralStress:
    """
    Servicio de aplicación para calcular el estrés estructural en nodos y runs.

    Modelo estructural:
    - Cada span genera una fuerza axial por pendiente.
    - Cada nodo se analiza como equilibrio entre:
        * Fuerza acumulada desde la izquierda
        * Fuerza acumulada desde la derecha
    - El desequilibrio genera tensión o compresión.
    """

    def __init__(
        self,
        max_tension_kN: float = 50.0,
        max_compression_kN: float = 30.0,
        g: float = 9.81,
    ) -> None:
        self._max_tension_kN = max_tension_kN
        self._max_compression_kN = max_compression_kN
        self._g = g

    def execute(
        self,
        request_id: UUID,
        longitudinal: LongitudinalSlopeAnalysis,
        config: ThresholdConfig,
    ) -> StructuralStressAnalysis:
        nodes: List[NodeStressResult] = []
        runs: List[StressRunResult] = []

        # Agrupar spans por azimuth
        spans_by_azimuth: Dict[float, List[SpanSlopeResult]] = {}

        for span in longitudinal.spans:
            spans_by_azimuth.setdefault(span.azimuth_deg, []).append(span)

        for azimuth, spans in spans_by_azimuth.items():
            spans = sorted(spans, key=lambda s: s.span_index)

            span_forces = [self._calculate_span_force(span) for span in spans]

            prefix_forces: List[float] = []
            acc = 0.0
            for force in span_forces:
                acc += force
                prefix_forces.append(acc)

            suffix_forces: List[float] = [0.0] * len(span_forces)
            acc = 0.0
            for idx in reversed(range(len(span_forces))):
                acc += span_forces[idx]
                suffix_forces[idx] = acc

            for i in range(len(spans) + 1):
                span_in = spans[i - 1] if i > 0 else spans[0]
                span_out = spans[i] if i < len(spans) else spans[-1]

                #  Pivot Point
                if i == 0:
                    left_force = 0.0
                    right_force = suffix_forces[0]

                #  Nodo extremo (después del último span)
                elif i == len(spans):
                    left_force = prefix_forces[-1]
                    right_force = 0.0

                #  Nodos interiores
                else:
                    left_force = prefix_forces[i - 1]
                    right_force = suffix_forces[i]

                (
                    internal_force,
                    force_type,
                    safety_factor,
                    is_critical,
                ) = self._calculate_node_force(
                    left_force=left_force,
                    right_force=right_force,
                )

                if 0 < i < len(spans):
                    delta_pct = span_out.slope.pct - span_in.slope.pct
                else:
                    delta_pct = 0.0

                if delta_pct > 0:
                    kind = NodeKind.VALLEY
                elif delta_pct < 0:
                    kind = NodeKind.CREST
                else:
                    kind = NodeKind.NEUTRAL

                delta = SlopeValue.from_pct(delta_pct)
                classification = config.classify(abs(delta_pct))

                valley_double_check = (
                    kind == NodeKind.VALLEY and abs(delta_pct) > 2 * config.max_value
                )

                nodes.append(
                    NodeStressResult(
                        azimuth_deg=azimuth,
                        tower_index=i,
                        radius_m=span_in.radius_end_m if i > 0 else 0.0,
                        slope_in=span_in.slope,
                        slope_out=span_out.slope,
                        delta=delta,
                        node_kind=kind,
                        classification=classification,
                        valley_double_check=valley_double_check,
                        left_force_kN=left_force,
                        right_force_kN=right_force,
                        internal_force_kN=internal_force,
                        force_type=force_type,
                        safety_factor=safety_factor,
                        is_critical=is_critical,
                    )
                )

                if is_critical:
                    logger.warning(
                        f"Nodo crítico: "
                        f"azimuth={azimuth}, "
                        f"torre={i + 1}, "
                        f"left={left_force:.2f} kN, "
                        f"right={right_force:.2f} kN, "
                        f"internal={internal_force:.2f} kN, "
                        f"tipo={force_type}"
                    )

            # Construcción de runs
            current_run: List[SpanSlopeResult] = []

            for span in spans:
                if not current_run or span.slope.pct * current_run[-1].slope.pct > 0:
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

            # Último run
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

        return StructuralStressAnalysis(
            request_id=request_id,
            nodes=nodes,
            runs=runs,
        )

    def _calculate_span_force(
        self,
        span: SpanSlopeResult,
    ) -> float:
        """
        Fuerza axial individual de un span.

        Fórmula:
        """

        weight_kN = span.service_weight * self._g / 1000.0
        slope_rad = math.radians(span.slope.deg)

        return weight_kN * math.sin(slope_rad)

    def _calculate_node_force(
        self,
        left_force: float,
        right_force: float,
    ) -> tuple[float, RunKind, float, bool]:
        """
        Fuerza interna del nodo por equilibrio.
        """
        internal_force = right_force - left_force

        if internal_force > 0:
            force_type = RunKind.TENSION
            max_allowed = self._max_tension_kN

        elif internal_force < 0:
            force_type = RunKind.COMPRESSION
            max_allowed = self._max_compression_kN
            internal_force = abs(internal_force)

        else:
            return (
                0.0,
                RunKind.NEUTRAL,
                float("inf"),
                False,
            )

        safety_factor = max_allowed / internal_force
        is_critical = internal_force > max_allowed

        return (
            internal_force,
            force_type,
            safety_factor,
            is_critical,
        )
