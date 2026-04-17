"""OGC API discovery endpoints: landing page, conformance, collections and processes."""

from typing import Any

from fastapi import APIRouter

router = APIRouter(tags=["OGC API"])


@router.get("/", summary="OGC API Landing Page")
def landing_page() -> dict[str, Any]:
    return {
        "title": "AISCO Spatial Analysis API",
        "description": "Spatial analysis API following OGC API Features and OGC API Processes "
        "standards.",
        "links": [
            {"href": "/", "rel": "self", "type": "application/json", "title": "This document"},
            {
                "href": "/conformance",
                "rel": "conformance",
                "type": "application/json",
                "title": "Conformance classes",
            },
            {
                "href": "/collections",
                "rel": "data",
                "type": "application/json",
                "title": "Available collections",
            },
            {
                "href": "/processes",
                "rel": "processes",
                "type": "application/json",
                "title": "Available processes",
            },
        ],
    }


@router.get("/conformance", summary="OGC API Conformance Classes")
def conformance() -> dict[str, Any]:
    return {
        "conformsTo": [
            "http://www.opengis.net/spec/ogcapi-features-1/1.0/conf/core",
            "http://www.opengis.net/spec/ogcapi-features-1/1.0/conf/oas30",
            "http://www.opengis.net/spec/ogcapi-features-1/1.0/conf/geojson",
            "http://www.opengis.net/spec/ogcapi-processes-1/1.0/conf/core",
        ]
    }


@router.get("/collections", summary="OGC API Available Collections")
def list_collections() -> dict[str, Any]:
    return {
        "collections": [
            {
                "id": "zones",
                "title": "Zones",
                "description": "Geographic zones used for spatial analysis.",
                "links": [
                    {
                        "href": "/collections/zones/items",
                        "rel": "items",
                        "type": "application/geo+json",
                    }
                ],
            },
            {
                "id": "zone-analyses",
                "title": "Zone Elevation Analyses",
                "description": "Elevation analysis results per zone.",
                "links": [
                    {
                        "href": "/collections/zone-analyses/items",
                        "rel": "items",
                        "type": "application/geo+json",
                    }
                ],
            },
            {
                "id": "zone-contours",
                "title": "Zone Elevation Contours",
                "description": "Elevation contour lines per zone.",
                "links": [
                    {
                        "href": "/collections/zone-contours/items",
                        "rel": "items",
                        "type": "application/geo+json",
                    }
                ],
            },
        ]
    }


@router.get("/processes", summary="OGC API Available Processes")
def list_processes() -> dict[str, Any]:
    return {
        "processes": [
            {
                "id": "highest-point",
                "title": "Highest Point",
                "description": "Get the highest elevation point within a polygon or zone.",
                "version": "1.0.0",
                "jobControlOptions": ["sync-execute"],
                "links": [
                    {
                        "href": "/processes/highest-point/execution",
                        "rel": "execute",
                        "type": "application/json",
                    }
                ],
            },
            {
                "id": "point-elevation",
                "title": "Point Elevation",
                "description": "Get the elevation at a specific geographic point.",
                "version": "1.0.0",
                "jobControlOptions": ["sync-execute"],
                "links": [
                    {
                        "href": "/processes/point-elevation/execution",
                        "rel": "execute",
                        "type": "application/json",
                    }
                ],
            },
            {
                "id": "analyze-zone-elevation",
                "title": "Analyze Zone Elevation",
                "description": "Analyse elevation for a zone and persist characteristic points"
                " (highest, lowest, centroid).",
                "version": "1.0.0",
                "jobControlOptions": ["sync-execute"],
                "links": [
                    {
                        "href": "/processes/analyze-zone-elevation/execution",
                        "rel": "execute",
                        "type": "application/json",
                    }
                ],
            },
            {
                "id": "generate-zone-contours",
                "title": "Generate Zone Contours",
                "description": "Generate and persist elevation contour lines for a zone.",
                "version": "1.0.0",
                "jobControlOptions": ["sync-execute"],
                "links": [
                    {
                        "href": "/processes/generate-zone-contours/execution",
                        "rel": "execute",
                        "type": "application/json",
                    }
                ],
            },
        ]
    }
