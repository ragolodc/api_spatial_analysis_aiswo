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

    client.command(
        f"""
            CREATE TABLE IF NOT EXISTS {database}.transversal_slope_analysis (
                request_id UUID,
                zone_id UUID,
                profile_analysis_id UUID,
                radius_m Float64,
                azimuth_from_deg Float64,
                azimuth_to_deg Float64,
                arc_length_m Float64,
                slope_pct Float64,
                slope_deg Float64,
                classification String
            )
            ENGINE = MergeTree
            ORDER BY (request_id, profile_analysis_id, radius_m)
            """
    )

    client.command(
        f"""
            CREATE TABLE IF NOT EXISTS {database}.torsional_slope_analysis (
                request_id UUID,
                zone_id UUID,
                profile_analysis_id UUID,
                azimuth_deg Float64,
                span_index UInt32,
                radius_start_m Float64,
                radius_end_m Float64,
                alpha_inner_pct Float64,
                alpha_inner_deg Float64,
                alpha_outer_pct Float64,
                alpha_outer_deg Float64,
                torsion_pct Float64,
                torsion_deg Float64,
                longitudinal_slope_pct Float64,
                longitudinal_slope_deg Float64,
                combined_load_index Float64,
                classification String
            )
            ENGINE = MergeTree
            ORDER BY (request_id, profile_analysis_id, span_index)
            """
    )

    client.command(
        f"""CREATE TABLE IF NOT EXISTS {database}.structural_stress_nodes (
            request_id UUID,
            zone_id UUID,
            profile_analysis_id UUID,
            azimuth_deg Float64,
            tower_index UInt32,
            radius_m Float64,
            slope_in_pct Float64,
            slope_in_deg Float64,
            slope_out_pct Float64,
            slope_out_deg Float64,
            delta_pct Float64,
            delta_deg Float64,
            node_kind String,
            classification String,
            valley_double_check UInt8
        )
        ENGINE = MergeTree
        ORDER BY (request_id, profile_analysis_id, azimuth_deg)
        """
    )

    client.command(
        f"""CREATE TABLE IF NOT EXISTS {database}.structural_stress_runs (
            request_id UUID,
            zone_id UUID,
            profile_analysis_id UUID,
            azimuth_deg Float64,
            run_kind String,
            span_indices String,
            cumulative_slope_pct Float64
        )
        ENGINE = MergeTree
        ORDER BY (request_id, profile_analysis_id, azimuth_deg)
        """
    )

    client.command(
        f"""CREATE TABLE IF NOT EXISTS {database}.crop_clearance_analysis (
            "request_id" UUID,
            "zone_id" UUID,
            "profile_analysis_id" UUID,
            "azimuth_deg" Float64,
            "distance_m" Float64,
            "boom_elevation_m" Float64,
            "terrain_elevation_m" Float64,
            "clearance_m" Float64,
            "classification" String,
            "in_valley_node" UInt8
        )
        ENGINE = MergeTree
        ORDER BY (request_id, profile_analysis_id, distance_m)
        """
    )
