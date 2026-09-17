import json
from pathlib import Path
from typing import Iterator


def stream_logs(file_path: str) -> Iterator[dict]:
    """Read JSONL logs one event at a time."""

    path = Path(file_path)

    with path.open("r", encoding="utf-8", errors="replace") as file:
        for line_number, line in enumerate(file, start=1):
            line = line.strip()

            if not line:
                continue

            try:
                yield json.loads(line)

            except json.JSONDecodeError as error:
                print(
                    f"Invalid JSON at line {line_number}: {error}"
                )
