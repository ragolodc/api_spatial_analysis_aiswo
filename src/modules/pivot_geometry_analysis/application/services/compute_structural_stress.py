import logging
import math
from typing import Optional
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

    Modelo estructural mejorado:
    - Cada span genera una fuerza axial por pendiente: F = W_total * sin(θ)
    - W_total incluye peso propio del span, agua y accesorios (service_weight en kg).
    - La fuerza axial se acumula desde el extremo libre hacia el pivote.
    - En cada torre (nodo), la fuerza neta horizontal es la diferencia entre la fuerza
      acumulada a la derecha y la izquierda (right_force - left_force).
    - Si la fuerza neta es positiva, la torre está en tensión; negativa, en compresión.
    - Además, se calcula la carga crítica de pandeo para spans en compresión,
      usando la fórmula de Euler (columna biarticulada) con longitud efectiva.
    - Los runs (secuencias continuas) se definen por el signo de la fuerza axial
      de cada span, no por el signo de la pendiente.
    """

    def __init__(
        self,
        max_tension_kN: float = 50.0,
        max_compression_kN: float = 30.0,
        g: float = 9.81,
        tower_mass_kg: float = 0.0,  # masa de cada torre (kg), opcional
        enable_pandeo: bool = True,  # activar verificación de pandeo
        E_steel_GPa: float = 200.0,  # módulo de elasticidad (GPa)
        pipe_diameter_m: float = 0.2,  # diámetro exterior (m)
        pipe_thickness_m: float = 0.005,  # espesor (m)
        buckling_safety_factor: float = 2.0,  # factor de seguridad para pandeo
    ) -> None:
        self._max_tension_kN = max_tension_kN
        self._max_compression_kN = max_compression_kN
        self._g = g
        self._tower_mass_kg = tower_mass_kg
        self._enable_pandeo = enable_pandeo
        self._E = E_steel_GPa * 1e9  # Pa
        self._d = pipe_diameter_m
        self._t = pipe_thickness_m
        self._buckling_fs = buckling_safety_factor

    def execute(
        self,
        request_id: UUID,
        longitudinal: LongitudinalSlopeAnalysis,
        config: ThresholdConfig,
        max_tension_kN: Optional[float] = None,
        max_compression_kN: Optional[float] = None,
    ) -> StructuralStressAnalysis:
        _tension_limit = max_tension_kN if max_tension_kN is not None else self._max_tension_kN
        _compression_limit = max_compression_kN if max_compression_kN is not None else self._max_compression_kN
        nodes: list[NodeStressResult] = []
        runs: list[StressRunResult] = []

        spans_by_azimuth: dict[float, list[SpanSlopeResult]] = {}
        for span in longitudinal.spans:
            spans_by_azimuth.setdefault(span.azimuth_deg, []).append(span)

        for azimuth, spans in spans_by_azimuth.items():
            spans = sorted(spans, key=lambda s: s.span_index)
            n = len(spans)

            # 1. Fuerza axial individual de cada span (con signo)
            #    Positiva = tensión, negativa = compresión.
            span_forces = [self._calculate_span_force(span) for span in spans]

            # 2. Acumulación desde el extremo libre (hacia la izquierda o derecha)
            #    prefix_forces[i] = suma de span_forces[0..i] (desde pivote hacia afuera)
            #    suffix_forces[i] = suma de span_forces[i..n-1] (desde el extremo hacia pivote)
            prefix_forces = []
            acc = 0.0
            for force in span_forces:
                acc += force
                prefix_forces.append(acc)

            suffix_forces = [0.0] * n
            acc = 0.0
            for idx in range(n - 1, -1, -1):
                acc += span_forces[idx]
                suffix_forces[idx] = acc

            # 3. Recorrer nodos (i=0 es pivote, i=n es extremo libre)
            for i in range(n + 1):
                # --- Fuerzas izquierda/derecha (axiales en los tramos adyacentes) ---
                if i == 0:
                    left_force = 0.0
                    right_force = suffix_forces[0]  # suma total
                elif i == n:
                    left_force = prefix_forces[-1]
                    right_force = 0.0
                else:
                    left_force = prefix_forces[i - 1]
                    right_force = suffix_forces[i]

                # --- Fuerza neta en el nodo (torre o anclaje) ---
                net_force = right_force - left_force  # positiva = tensión, negativa = compresión

                # --- Parámetros adicionales para pandeo y clasificación ---
                span_under_compression = None  # span que recibe compresión crítica
                if i > 0 and i < n and net_force < 0 and self._enable_pandeo:
                    # El nodo está en compresión. El span que más sufre será el que tenga
                    # mayor fuerza de compresión (el de la izquierda o derecha según el signo)
                    # Para simplificar, evaluamos el span con mayor compresión entre los dos adyacentes.
                    candidate_span = None
                    max_comp = 0.0
                    if left_force < 0 and abs(left_force) > max_comp:
                        max_comp = abs(left_force)
                        candidate_span = spans[i - 1]
                    if right_force < 0 and abs(right_force) > max_comp:
                        max_comp = abs(right_force)
                        candidate_span = spans[i] if i < n else None
                    span_under_compression = candidate_span

                # --- Clasificar el nodo (valle/cresta/neutral) ---
                if 0 < i < n:
                    span_in = spans[i - 1]
                    span_out = spans[i]
                    delta_pct = span_out.slope.pct - span_in.slope.pct
                else:
                    delta_pct = 0.0
                    span_in = spans[0] if n > 0 else None
                    span_out = spans[-1] if n > 0 else None

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

                # --- Calcular fuerza interna, tipo, factor de seguridad y si es crítico ---
                internal_force_magnitude, force_type, safety_factor, is_critical = (
                    self._evaluate_node_force(
                        net_force=net_force,
                        span_compression=span_under_compression,
                        max_tension_kN=_tension_limit,
                        max_compression_kN=_compression_limit,
                    )
                )

                # radio del nodo (posición a lo largo del pivote)
                radius_m = span_in.radius_end_m if i > 0 else 0.0

                nodes.append(
                    NodeStressResult(
                        azimuth_deg=azimuth,
                        tower_index=i,
                        radius_m=radius_m,
                        slope_in=span_in.slope if span_in else spans[0].slope,
                        slope_out=span_out.slope if span_out else spans[-1].slope,
                        delta=delta,
                        node_kind=kind,
                        classification=classification,
                        valley_double_check=valley_double_check,
                        left_force_kN=left_force,
                        right_force_kN=right_force,
                        internal_force_kN=internal_force_magnitude,  # siempre positivo
                        force_type=force_type,
                        safety_factor=safety_factor,
                        is_critical=is_critical,
                    )
                )

                if is_critical:
                    logger.warning(
                        f"Nodo crítico: azimuth={azimuth:.2f}, torre={i}, "
                        f"net_force={net_force:.2f} kN, tipo={force_type}, "
                        f"left={left_force:.2f}, right={right_force:.2f}"
                    )

            # --- Run de spans basado en el signo de la fuerza axial (mejorado) ---
            runs_azimuth = self._build_runs_from_forces(azimuth, spans, span_forces)
            runs.extend(runs_azimuth)

        return StructuralStressAnalysis(
            request_id=request_id,
            nodes=nodes,
            runs=runs,
        )

    def _calculate_span_force(self, span: SpanSlopeResult) -> float:
        """
        Calcula la componente axial longitudinal del span.
        Se asume que span.service_weight es el peso TOTAL del span (kg)
        incluyendo tubería, agua, accesorios, etc.

        Retorna fuerza en kN.
        Signo: positivo cuando la tendencia es a tensión (pendiente negativa? Cuidado)
        La fórmula es F = (W_total_kg * g / 1000) * sin(θ)
        donde θ es el ángulo de la pendiente (positivo = subiendo).
        Física: si la pendiente es positiva (sube), el peso tira hacia atrás (compresión)
        porque la componente es hacia abajo y atrás. En nuestro criterio:
        - Pendiente positiva -> fuerza_axial negativa (compresión)
        - Pendiente negativa -> fuerza_axial positiva (tensión)
        """
        weight_kN = span.service_weight * self._g / 1000.0
        slope_rad = math.radians(span.slope.deg)
        return -weight_kN * math.sin(slope_rad)

    def _buckling_load(self, length_m: float) -> float:
        """
        Calcula la carga crítica de pandeo de Euler para una columna biarticulada.
        Retorna en kN.
        """
        # Momento de inercia para tubería circular hueca
        # I = π/64 * (D^4 - d^4)
        D = self._d
        d = D - 2 * self._t
        if d <= 0:
            d = 0.001  # evitar división por cero
        I = (math.pi / 64.0) * (D**4 - d**4)
        # Carga crítica (N)
        P_crit = (math.pi**2 * self._E * I) / (length_m**2)
        # Convertir a kN
        return P_crit / 1000.0

    def _evaluate_node_force(
        self,
        net_force: float,
        span_compression: Optional[SpanSlopeResult] = None,
        max_tension_kN: Optional[float] = None,
        max_compression_kN: Optional[float] = None,
    ) -> tuple[float, str, float, bool]:
        """
        Evalúa la fuerza neta en el nodo (torre o anclaje).
        net_force > 0: tensión, < 0: compresión.
        Retorna (magnitud, tipo, safety_factor, is_critical).
        Incluye verificación de pandeo si corresponde.
        """
        magnitude = abs(net_force)
        if magnitude < 1e-6:
            return (0.0, "neutral", float("inf"), False)

        _tension = max_tension_kN if max_tension_kN is not None else self._max_tension_kN
        _compression = max_compression_kN if max_compression_kN is not None else self._max_compression_kN

        if net_force > 0:
            force_type = "tension"
            max_allowed = _tension
            safety = max_allowed / magnitude
            critical = magnitude > max_allowed
            return (magnitude, force_type, safety, critical)
        else:
            force_type = "compression"
            max_allowed_force = _compression
            # Verificar pandeo si está activado y tenemos información del span
            buckling_load = None
            if self._enable_pandeo and span_compression is not None:
                length_span = span_compression.radius_end_m - span_compression.radius_start_m
                if length_span > 0:
                    buckling_load = self._buckling_load(length_span) / self._buckling_fs
            if buckling_load is not None and buckling_load > 0:
                max_allowed = min(max_allowed_force, buckling_load)
            else:
                max_allowed = max_allowed_force

            safety = max_allowed / magnitude if max_allowed > 0 else 0.0
            critical = magnitude > max_allowed
            return (magnitude, force_type, safety, critical)

    def _build_runs_from_forces(
        self, azimuth: float, spans: list[SpanSlopeResult], span_forces: list[float]
    ) -> list[StressRunResult]:
        """
        Construye runs basados en el signo de span_forces (fuerza axial).
        Un run es una secuencia de 2 o más spans consecutivos con el mismo signo de fuerza.
        """
        runs = []
        n = len(spans)
        idx = 0
        while idx < n:
            # Buscar el signo actual (ignorando fuerzas casi nulas)
            sign = 0
            start = idx
            while start < n and abs(span_forces[start]) < 1e-6:
                start += 1
            if start >= n:
                break
            sign = 1 if span_forces[start] > 0 else -1
            # Avanzar mientras el signo se mantenga
            end = start + 1
            while end < n and (span_forces[end] * sign > 0 or abs(span_forces[end]) < 1e-6):
                end += 1
            # Si hay al menos dos spans con el mismo signo (ignorando los neutros)
            count = 0
            for k in range(start, end):
                if abs(span_forces[k]) >= 1e-6 and (span_forces[k] * sign > 0):
                    count += 1
            if count >= 2:
                # Recoger los índices reales de los spans que tienen el signo
                indices = [
                    k
                    for k in range(start, end)
                    if abs(span_forces[k]) >= 1e-6 and span_forces[k] * sign > 0
                ]
                kind_run = RunKind.TENSION if sign > 0 else RunKind.COMPRESSION
                runs.append(
                    StressRunResult(
                        azimuth_deg=azimuth,
                        run_kind=kind_run,
                        span_indices=indices,
                        cumulative_slope_pct=sum(spans[k].slope.pct for k in indices),
                    )
                )
            idx = end
        return runs
