import clickhouse_connect.driver


def ensure_schema(client: clickhouse_connect.driver.Client, database: str) -> None:
    client.command(f"CREATE DATABASE IF NOT EXISTS {database}")
    client.command(
        f"""
            CREATE TABLE IF NOT EXISTS {database}.longitudinal_slope_analysis (
                request_id UUID,
                zone_id UUID,
                profile_analysis_id UUID,
                azimuth_deg Float64,
                span_index UInt32,
                radius_start_m Float64,
                radius_end_m Float64,
                slope_pct Float64,
                slope_deg Float64,
                classification String
            )
            ENGINE = MergeTree
            ORDER BY (request_id, profile_analysis_id, span_index)
            """
    )
