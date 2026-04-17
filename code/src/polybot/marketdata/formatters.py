import csv
import json
from io import StringIO
from typing import Literal, Sequence

from pydantic import BaseModel


def format_records(
    records: Sequence[BaseModel],
    output: Literal["table", "json", "csv"] = "table",
) -> str:
    rows = [record.model_dump(mode="json") for record in records]
    if output == "json":
        return json.dumps(rows, ensure_ascii=False, indent=2)
    if not rows:
        return ""

    fields = list(rows[0].keys())
    if output == "csv":
        buffer = StringIO()
        writer = csv.DictWriter(buffer, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
        return buffer.getvalue().rstrip("\n")
    if output == "table":
        lines = ["\t".join(fields)]
        lines.extend("\t".join(_display(row.get(field)) for field in fields) for row in rows)
        return "\n".join(lines)
    raise ValueError(f"unsupported output format: {output}")


def _display(value: object) -> str:
    return "" if value is None else str(value)
