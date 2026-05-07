import csv
from pathlib import Path

class CSVExporter:
    """Stub exporter for saving application data to CSV."""

    def export(self, data: dict, output_path: Path) -> Path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with output_path.open("w", newline="", encoding="utf-8") as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(data.keys())
            writer.writerow(data.values())
        return output_path
