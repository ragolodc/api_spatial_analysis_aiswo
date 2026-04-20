"""Domain-to-schema mapping helpers shared between collection and process routers."""

from src.modules.elevation_analysis.domain.entities import ElevationAnalysis, ElevationContour
from src.modules.elevation_analysis.presentation.schemas import (
    AnalysisProperties,
    ContourProperties,
    ElevationAnalysisFeature,
    ElevationContourCollection,
    ElevationContourFeature,
    ElevationPointFeature,
    ElevationPointProperties,
    MultiLineStringGeometry,
    PointGeometry,
)


def analysis_to_feature(analysis: ElevationAnalysis) -> ElevationAnalysisFeature:
    points = [
        ElevationPointFeature(
            id=str(p.id),
            geometry=PointGeometry(coordinates=[p.longitude, p.latitude]),
            properties=ElevationPointProperties(
                point_type=p.point_type,
                elevation_m=p.elevation_m,
                analysis_id=p.analysis_id,
            ),
        )
        for p in analysis.points
    ]
    return ElevationAnalysisFeature(
        id=str(analysis.id),
        properties=AnalysisProperties(
            zone_id=analysis.zone_id,
            source_id=analysis.source_id,
            analyzed_at=analysis.analyzed_at.isoformat(),
        ),
        characteristic_points=points,
    )


def contours_to_collection(contours: list[ElevationContour]) -> ElevationContourCollection:
    features = [
        ElevationContourFeature(
            id=str(c.id),
            geometry=MultiLineStringGeometry(coordinates=c.geometry.coordinates),
            properties=ContourProperties(
                zone_id=c.zone_id,
                elevation_m=c.elevation_m,
                interval_m=c.interval_m,
                source_id=c.source_id,
                generated_at=c.generated_at.isoformat(),
            ),
        )
        for c in contours
    ]
    return ElevationContourCollection(features=features, number_matched=len(features))
