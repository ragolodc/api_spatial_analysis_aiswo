from dataclasses import dataclass
from typing import Dict, List, Tuple

import clickhouse_connect.driver


@dataclass(frozen=True)
class TableDefinition:
    """Define la estructura de una tabla de ClickHouse"""

    name: str
    columns: List[Tuple[str, str]]  # (nombre, tipo)
    order_by: List[str]
    description: str = ""


TABLE_DEFINITIONS = {
    "longitudinal_slope_analysis": TableDefinition(
        name="longitudinal_slope_analysis",
        columns=[
            ("request_id", "UUID"),
            ("zone_id", "UUID"),
            ("profile_analysis_id", "UUID"),
            ("azimuth_deg", "Float64"),
            ("span_index", "UInt32"),
            ("radius_start_m", "Float64"),
            ("radius_end_m", "Float64"),
            ("slope_pct", "Float64"),
            ("slope_deg", "Float64"),
            ("service_weight", "Float64"),
            ("classification", "String"),
        ],
        order_by=["request_id", "profile_analysis_id", "span_index"],
        description="Análisis de pendiente longitudinal por tramo",
    ),
    "transversal_slope_analysis": TableDefinition(
        name="transversal_slope_analysis",
        columns=[
            ("request_id", "UUID"),
            ("zone_id", "UUID"),
            ("profile_analysis_id", "UUID"),
            ("radius_m", "Float64"),
            ("azimuth_from_deg", "Float64"),
            ("azimuth_to_deg", "Float64"),
            ("arc_length_m", "Float64"),
            ("slope_pct", "Float64"),
            ("slope_deg", "Float64"),
            ("classification", "String"),
        ],
        order_by=["request_id", "profile_analysis_id", "radius_m"],
        description="Análisis de pendiente transversal",
    ),
    "torsional_slope_analysis": TableDefinition(
        name="torsional_slope_analysis",
        columns=[
            ("request_id", "UUID"),
            ("zone_id", "UUID"),
            ("profile_analysis_id", "UUID"),
            ("azimuth_deg", "Float64"),
            ("span_index", "UInt32"),
            ("radius_start_m", "Float64"),
            ("radius_end_m", "Float64"),
            ("alpha_inner_pct", "Float64"),
            ("alpha_inner_deg", "Float64"),
            ("alpha_outer_pct", "Float64"),
            ("alpha_outer_deg", "Float64"),
            ("torsion_pct", "Float64"),
            ("torsion_deg", "Float64"),
            ("longitudinal_slope_pct", "Float64"),
            ("longitudinal_slope_deg", "Float64"),
            ("combined_load_index", "Float64"),
            ("classification", "String"),
        ],
        order_by=["request_id", "profile_analysis_id", "span_index"],
        description="Análisis de pendiente torsional",
    ),
    "structural_stress_nodes": TableDefinition(
        name="structural_stress_nodes",
        columns=[
            ("request_id", "UUID"),
            ("zone_id", "UUID"),
            ("profile_analysis_id", "UUID"),
            ("azimuth_deg", "Float64"),
            ("tower_index", "UInt32"),
            ("radius_m", "Float64"),
            ("slope_in_pct", "Float64"),
            ("slope_in_deg", "Float64"),
            ("slope_out_pct", "Float64"),
            ("slope_out_deg", "Float64"),
            ("delta_pct", "Float64"),
            ("delta_deg", "Float64"),
            ("node_kind", "String"),
            ("classification", "String"),
            ("valley_double_check", "UInt8"),
            ("left_force_kN", "Float64"),
            ("right_force_kN", "Float64"),
            ("internal_force_kN", "Float64"),
            ("force_type", "String"),
            ("safety_factor", "Float64"),
            ("is_critical", "UInt8"),
        ],
        order_by=["request_id", "profile_analysis_id", "azimuth_deg"],
        description="Nodos de estrés estructural",
    ),
    "structural_stress_runs": TableDefinition(
        name="structural_stress_runs",
        columns=[
            ("request_id", "UUID"),
            ("zone_id", "UUID"),
            ("profile_analysis_id", "UUID"),
            ("azimuth_deg", "Float64"),
            ("run_kind", "String"),
            ("span_indices", "String"),
            ("cumulative_slope_pct", "Float64"),
        ],
        order_by=["request_id", "profile_analysis_id", "azimuth_deg"],
        description="Secuencias de estrés estructural",
    ),
    "crop_clearance_analysis": TableDefinition(
        name="crop_clearance_analysis",
        columns=[
            ("request_id", "UUID"),
            ("zone_id", "UUID"),
            ("profile_analysis_id", "UUID"),
            ("azimuth_deg", "Float64"),
            ("distance_m", "Float64"),
            ("boom_elevation_m", "Float64"),
            ("terrain_elevation_m", "Float64"),
            ("clearance_m", "Float64"),
            ("classification", "String"),
            ("in_valley_node", "UInt8"),
        ],
        order_by=["request_id", "profile_analysis_id", "distance_m"],
        description="Análisis de despacho (clearance) en cultivos",
    ),
}


def _safe_identifier(name: str) -> str:
    """Escapa identificadores para evitar SQL injection"""
    return f'"{name.replace('"', '""')}"'


def _create_table_sql(database: str, table_def: TableDefinition) -> str:
    """Genera SQL para crear una tabla"""
    columns_sql = ",\n    ".join(
        f"{_safe_identifier(col_name)} {col_type}" for col_name, col_type in table_def.columns
    )

    return f"""
        CREATE TABLE IF NOT EXISTS {_safe_identifier(database)}.{_safe_identifier(table_def.name)} (
            {columns_sql}
        )
        ENGINE = MergeTree
        ORDER BY ({", ".join(_safe_identifier(col) for col in table_def.order_by)})
    """


def ensure_database_exists(client: clickhouse_connect.driver.Client, database: str) -> None:
    """Asegura que la base de datos existe"""
    client.command(f"CREATE DATABASE IF NOT EXISTS {_safe_identifier(database)}")


def create_table(
    client: clickhouse_connect.driver.Client, database: str, table_def: TableDefinition
) -> None:
    """Crea una tabla si no existe"""
    sql = _create_table_sql(database, table_def)
    client.command(sql)


def ensure_all_tables(
    client: clickhouse_connect.driver.Client, database: str, tables: Dict[str, TableDefinition]
) -> None:
    """Asegura que todas las tablas existen"""
    ensure_database_exists(client, database)

    for table_def in tables.values():
        create_table(client, database, table_def)


def ensure_schema(client: clickhouse_connect.driver.Client, database: str) -> None:
    ensure_all_tables(client, database, TABLE_DEFINITIONS)
