import logging
from dataclasses import dataclass
from functools import lru_cache
from typing import Any, Dict, Optional

from src.modules.pivot_geometry_analysis.application.services import (
    ComputeCropClearance,
    ComputeLongitudinalSlope,
    ComputeStructuralStress,
    ComputeTorsionalSlope,
    ComputeTransversalSlope,
)
from src.modules.pivot_geometry_analysis.domain.entities import (
    SlopeAnalysisJobRequest,
    SlopeAnalysisResult,
)
from src.modules.pivot_geometry_analysis.domain.ports import ProfileReader
from src.modules.pivot_geometry_analysis.domain.value_objects import ThresholdConfig
from src.modules.profile_analysis.domain.entities import LongitudinalProfile, TransverseProfile

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class AnalysisConfig:
    """Configuración centralizada para todos los análisis"""

    longitudinal_slope_max_threshold: int = 18
    transversal_slope_max_threshold: int = 18
    torsional_max_threshold: int = 18
    torsional_longitudinal_max_threshold: int = 18
    structural_stress_max_threshold: int = 23
    crop_clearance_h_boom_meters: float = 2.90
    crop_clearance_crop_risk_meters: float = 2.0
    crop_clearance_ground_risk_meters: float = 1.0

    @classmethod
    def from_payload(cls, payload: Dict[str, Any]) -> "AnalysisConfig":
        """Extrae configuración del payload con valores por defecto"""
        inputs = payload.get("inputs", payload)

        # Valores por defecto definidos en la dataclass
        defaults = {f.name: f.default for f in cls.__dataclass_fields__.values()}

        # Extraer y limpiar valores
        config_dict = {}
        for field_name, default_value in defaults.items():
            value = inputs.get(field_name, default_value)
            config_dict[field_name] = default_value if value is None else value

        return cls(**config_dict)

    def to_threshold_configs(self) -> Dict[str, ThresholdConfig]:
        """Convierte a objetos ThresholdConfig"""
        return {
            "longitudinal": ThresholdConfig(self.longitudinal_slope_max_threshold),
            "transversal": ThresholdConfig(self.transversal_slope_max_threshold),
            "torsional": ThresholdConfig(self.torsional_max_threshold),
            "torsional_longitudinal": ThresholdConfig(self.torsional_longitudinal_max_threshold),
            "structural_stress": ThresholdConfig(self.structural_stress_max_threshold),
        }


class RunSlopeAnalysis:
    """
    Orquestador de análisis de pendientes para sistemas de riego por pivote.

    Responsabilidades:
    - Coordinar la ejecución secuencial de 5 análisis especializados
    - Gestionar la lectura de perfiles y configuración
    - Ensamblar el resultado final
    """

    def __init__(
        self,
        profile_reader: ProfileReader,
        crop_clearance_computator: Optional[ComputeCropClearance] = None,
        longitudinal_slope_computator: Optional[ComputeLongitudinalSlope] = None,
        transverse_slope_computator: Optional[ComputeTransversalSlope] = None,
        torsional_slope_computator: Optional[ComputeTorsionalSlope] = None,
        structural_stress_computator: Optional[ComputeStructuralStress] = None,
    ) -> None:
        self._profile_reader = profile_reader
        self._crop_clearance = crop_clearance_computator or ComputeCropClearance()
        self._longitudinal_slope = longitudinal_slope_computator or ComputeLongitudinalSlope()
        self._transverse_slope = transverse_slope_computator or ComputeTransversalSlope()
        self._torsional_slope = torsional_slope_computator or ComputeTorsionalSlope()
        self._structural_stress = structural_stress_computator or ComputeStructuralStress()
        self._analysis_chain = self._build_analysis_chain()

    def execute(self, request: SlopeAnalysisJobRequest) -> SlopeAnalysisResult:
        """
        Ejecuta el pipeline completo de análisis.

        Args:
            request: Solicitud de análisis con payload y metadatos

        Returns:
            Resultado consolidado de todos los análisis

        Raises:
            ValueError: Si faltan datos requeridos
            AnalysisError: Si falla algún análisis crítico
        """
        logger.info(f"Iniciando análisis para request_id={request.request_id}")

        # Validar entrada básica
        if not request.payload:
            raise ValueError("Payload vacío o inválido")

        # Cargar datos comunes (con logging)
        try:
            config = AnalysisConfig.from_payload(request.payload)
            logger.debug(f"Configuración cargada: {config}")

            longitudinal_profiles = self._profile_reader.get_longitudinal_profiles(
                request_id=request.profile_analysis_id
            )
            logger.debug(f"Perfiles longitudinales: {len(longitudinal_profiles)} puntos")

            transversal_profiles = self._profile_reader.get_transversal_profiles(
                request_id=request.profile_analysis_id
            )
            logger.debug(f"Perfiles transversales: {len(transversal_profiles)} puntos")

            spans_config = self._profile_reader.get_spans_configurations(
                request_id=request.profile_analysis_id
            )
            radii_m = spans_config.get_radii_m()
            logger.debug(f"Radios acumulados: {len(radii_m)} puntos")

        except Exception as e:
            logger.error(f"Error cargando datos: {e}", exc_info=True)
            raise ValueError(f"No se pudieron cargar los datos requeridos: {e}") from e

        # Ejecutar análisis secuenciales
        analysis_results = self._run_analysis_chain(
            request=request,
            config=config,
            longitudinal_profiles=longitudinal_profiles,
            transversal_profiles=transversal_profiles,
            radii_m=radii_m,
        )

        logger.info(f"Análisis completado exitosamente para request_id={request.request_id}")

        return SlopeAnalysisResult(request_id=request.request_id, **analysis_results)

    def _run_analysis_chain(
        self,
        request: SlopeAnalysisJobRequest,
        config: AnalysisConfig,
        longitudinal_profiles: list[LongitudinalProfile],
        transversal_profiles: list[TransverseProfile],
        radii_m: list[float],
    ):
        """Ejecuta la cadena de análisis respetando dependencias"""
        thresholds = config.to_threshold_configs()

        # Análisis 1: Pendiente longitudinal
        longitudinal = self._longitudinal_slope.execute(
            request_id=request.request_id,
            profiles=longitudinal_profiles,
            radii_m=radii_m,
            config=thresholds["longitudinal"],
        )

        # Análisis 2: Pendiente transversal
        transversal = self._transverse_slope.execute(
            request_id=request.request_id,
            profiles=transversal_profiles,
            config=thresholds["transversal"],
        )

        # Análisis 3: Pendiente torsional (depende de 1 y 2)
        torsional = self._torsional_slope.execute(
            request_id=request.request_id,
            longitudinal=longitudinal,
            transversal=transversal,
            torsion_config=thresholds["torsional"],
            longitudinal_config=thresholds["torsional_longitudinal"],
        )

        # Análisis 4: Estrés estructural (depende de 1)
        structural = self._structural_stress.execute(
            request_id=request.request_id,
            longitudinal=longitudinal,
            config=thresholds["structural_stress"],
        )

        # Análisis 5: Clearance de cultivo (depende de 4)
        crop_clearance = self._crop_clearance.execute(
            request_id=request.request_id,
            profiles=longitudinal_profiles,
            radii_m=radii_m,
            h_boom_m=config.crop_clearance_h_boom_meters,
            crop_risk_m=config.crop_clearance_crop_risk_meters,
            ground_risk_m=config.crop_clearance_ground_risk_meters,
            structural=structural,
        )

        return {
            "longitudinal_slope_analysis": longitudinal,
            "transversal_slope_analysis": transversal,
            "torsional_slope_analysis": torsional,
            "structural_stress_analysis": structural,
            "crop_clearance_analysis": crop_clearance,
        }

    @lru_cache(maxsize=1)
    def _build_analysis_chain(self) -> list:
        """Define el orden de ejecución de análisis (para posible inyección de dependencias)"""
        return [
            "longitudinal",
            "transversal",
            "torsional",
            "structural_stress",
            "crop_clearance",
        ]
