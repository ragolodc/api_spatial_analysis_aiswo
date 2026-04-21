import clickhouse_connect.driver


def ensure_schema(client: clickhouse_connect.driver.Client, database: str) -> None:
    client.command(f"CREATE DATABASE IF NOT EXISTS {database}")
    client.command(
        f"""
            CREATE TABLE IF NOT EXISTS {database}.profile_analysis_points (
                request_id UUID,
                zone_id UUID,
                profile_type LowCardinality(String),
                profile_key String,
                point_index UInt32,
                radius_m Float64,
                angle_deg Float64,
                distance_m Float64,
                longitude Float64,
                latitude Float64,
                elevation_m Nullable(Float64),
                source_id UUID
            )
            ENGINE = MergeTree
            ORDER BY (request_id, profile_type, profile_key, point_index)
            """
    )
