import math
from uuid import UUID

from src.modules.pivot_geometry_analysis.application.services._slope_math import arc_length
from src.modules.pivot_geometry_analysis.domain.entities import (
    TransversalSlopeAnalysis,
    TransversalSlopePoint,
)
from src.modules.pivot_geometry_analysis.domain.value_objects import SlopeValue, ThresholdConfig
from src.modules.profile_analysis.domain.entities import TransverseProfile


class ComputeTransversalSlope:
    def execute(
        self, request_id: UUID, profiles: list[TransverseProfile], config: ThresholdConfig
    ) -> TransversalSlopeAnalysis:
        arcs = []
        for profile in profiles:
            for i in range(len(profile.points) - 1):
                p_start = profile.points[i]
                p_end = profile.points[i + 1]

                delta_angle_rad = math.radians(p_end.angle_deg - p_start.angle_deg)
                dx = arc_length(p_start.radius_m, delta_angle_rad)

                if p_start.elevation_m is None or p_end.elevation_m is None:
                    continue

                dz = p_end.elevation_m - p_start.elevation_m

                slope = SlopeValue.from_ratio(dz=dz, dx=dx)
                classification = config.classify(slope.pct)

                arcs.append(
                    TransversalSlopePoint(
                        radius_m=p_start.radius_m,
                        azimuth_from_deg=p_start.angle_deg,
                        azimuth_to_deg=p_end.angle_deg,
                        arc_length_m=dx,
                        slope=slope,
                        classification=classification,
                    )
                )

        return TransversalSlopeAnalysis(request_id=request_id, points=arcs)
