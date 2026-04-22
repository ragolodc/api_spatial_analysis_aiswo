from uuid import UUID

from src.modules.pivot_geometry_analysis.domain.entities import (
    ClearancePoint,
    CropClearanceAnalysis,
    NodeKind,
    StructuralStressAnalysis,
)
from src.modules.profile_analysis.domain.entities import LongitudinalProfile


class ComputeCropClearance:
    def execute(
        self,
        request_id: UUID,
        profiles: list[LongitudinalProfile],
        radii_m: tuple[float, ...],
        h_boom_m: float,
        crop_risk_m: float,
        ground_risk_m: float,
        structural: StructuralStressAnalysis,
    ) -> CropClearanceAnalysis:

        valley_nodes: set[tuple[float, int]] = {
            (node.azimuth_deg, node.tower_index)
            for node in structural.nodes
            if node.node_kind == NodeKind.VALLEY
        }

        tower_radii = (0.0, *radii_m)
        points: list[ClearancePoint] = []

        for profile in profiles:
            points_by_radius = {p.radius_m: p for p in profile.points}

            z_towers: dict[float, float] = {}
            for r in tower_radii:
                pt = points_by_radius.get(r)
                if pt and pt.elevation_m is not None:
                    z_towers[r] = pt.elevation_m

            for pt in sorted(profile.points, key=lambda p: p.radius_m):
                if pt.elevation_m is None:
                    continue

                span_idx = None
                for i in range(len(tower_radii) - 1):
                    if tower_radii[i] <= pt.radius_m <= tower_radii[i + 1]:
                        span_idx = i
                        break
                if span_idx is None:
                    continue

                r_start = tower_radii[span_idx]
                r_end = tower_radii[span_idx + 1]

                if r_start not in z_towers or r_end not in z_towers:
                    continue

                t = (pt.radius_m - r_start) / (r_end - r_start)
                boom_z = (z_towers[r_start] + h_boom_m) * (1 - t) + (z_towers[r_end] + h_boom_m) * t

                clearance = boom_z - pt.elevation_m

                if clearance < ground_risk_m:
                    classification = "ground_risk"
                elif clearance < crop_risk_m:
                    classification = "crop_risk"
                else:
                    classification = "ok"

                in_valley = (profile.azimuth_deg, span_idx) in valley_nodes or (
                    profile.azimuth_deg,
                    span_idx + 1,
                ) in valley_nodes

                points.append(
                    ClearancePoint(
                        azimuth_deg=profile.azimuth_deg,
                        distance_m=pt.radius_m,
                        boom_elevation_m=boom_z,
                        terrain_elevation_m=pt.elevation_m,
                        clearance_m=clearance,
                        classification=classification,
                        in_valley_node=in_valley,
                    )
                )

        return CropClearanceAnalysis(request_id=request_id, points=points)
