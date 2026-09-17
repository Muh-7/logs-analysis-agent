from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq

from src.log_reader import stream_logs
from src.log_normalizer import normalize_log


def ingest_to_parquet(
    input_path: str,
    output_path: str,
    chunk_size: int = 100_000,
):
    """
    Stream JSONL logs, normalize them, and write them
    to Parquet in chunks without loading the full file into RAM.
    """

    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)

    writer = None
    chunk = []
    total = 0

    try:
        for raw_log in stream_logs(input_path):

            log = normalize_log(raw_log)

            # Nested arbitrary dictionaries are inconvenient for our
            # first analytical table, so don't store raw `data` yet.
            log.pop("data", None)

            chunk.append(log)

            if len(chunk) >= chunk_size:
                writer = _write_chunk(
                    chunk=chunk,
                    output_path=output,
                    writer=writer,
                )

                total += len(chunk)

                print(f"Processed {total:,} events")

                chunk.clear()

        # Remaining events
        if chunk:
            writer = _write_chunk(
                chunk=chunk,
                output_path=output,
                writer=writer,
            )

            total += len(chunk)

            print(f"Processed {total:,} events")

    finally:
        if writer is not None:
            writer.close()

    print(f"\nFinished: {total:,} events")
    print(f"Output: {output}")


def _write_chunk(
    chunk: list[dict],
    output_path: Path,
    writer,
):
    table = pa.Table.from_pylist(chunk, schema=LOG_SCHEMA)

    if writer is None:
        writer = pq.ParquetWriter(
            output_path,
            table.schema,
            compression="zstd",
        )

    writer.write_table(table)

    return writer


LOG_SCHEMA = pa.schema([
    ("timestamp", pa.string()),
    ("event_id", pa.string()),

    ("agent_id", pa.string()),
    ("agent_name", pa.string()),
    ("agent_ip", pa.string()),

    ("manager_name", pa.string()),
    ("decoder", pa.string()),
    ("location", pa.string()),

    ("rule_id", pa.string()),
    ("rule_level", pa.int64()),
    ("rule_description", pa.string()),

    ("source_ip", pa.string()),
    ("source_port", pa.string()),
    ("destination_ip", pa.string()),
    ("destination_port", pa.string()),

    ("source_user", pa.string()),
    ("destination_user", pa.string()),
    ("uid", pa.string()),

    ("http_method", pa.string()),
    ("http_status", pa.string()),
    ("http_host", pa.string()),
    ("http_uri", pa.string()),
    ("http_user_agent", pa.string()),
    ("http_referrer", pa.string()),
    ("http_upstream_status", pa.string()),
    ("http_sent_to", pa.string()),
    ("http_response_length", pa.string()),

    ("message", pa.string()),
])