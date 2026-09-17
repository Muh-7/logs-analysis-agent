from pathlib import Path

from src.duckdb_query import DuckDBLogQuery


PROJECT_ROOT = Path(__file__).resolve().parent.parent

PARQUET_PATH = (
    PROJECT_ROOT
    / "Data_Cyper"
    / "processed"
    / "logs_100k.parquet"
)


def investigate_ip(ip: str, activity_limit: int = 20) -> dict:
    """
    Investigate a source IP using aggregated statistics
    and recent raw events.

    This function is designed to become an Agent Tool later.
    """

    query = DuckDBLogQuery(PARQUET_PATH)

    try:
        summary = query.ip_summary(ip)
        activity = query.ip_activity(
            ip,
            limit=activity_limit,
        )

        return {
            "ip": ip,
            "summary": summary,
            "recent_activity": activity,
        }

    finally:
        query.close()