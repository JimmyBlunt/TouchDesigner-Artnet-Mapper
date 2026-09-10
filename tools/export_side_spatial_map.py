"""Export the measured Pixelblaze XYZ map as a reusable TD/FastLED-style lookup."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from pixelblaze_mapper.complete_side_rescan import complete_side_measurements
from pixelblaze_mapper.spatial_map import spatial_map_document


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--mapping",
        type=Path,
        default=Path("mappings/mapping_complete_new_0_1183_full_2026-08-24.json"),
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("mappings/side_spatial_lookup_complete_new_2026-08-24.json"),
    )
    parser.add_argument(
        "--raw-scan",
        type=Path,
        default=Path("mappings/sources/complete_new_0_1183_raw_2026-08-24.json"),
    )
    parser.add_argument(
        "--report",
        type=Path,
        default=Path("mappings/complete_new_0_1183_report.json"),
    )
    args = parser.parse_args()
    coordinates = json.loads(args.mapping.read_text(encoding="utf-8"))
    raw_scan = json.loads(args.raw_scan.read_text(encoding="utf-8"))
    # Rebuild the calibration lattice from the scanner coordinate space.  The
    # cabinet-aligned mapping remains the authoritative XYZ used by effects and
    # the preview, but it must not be used to infer physical LED rows/columns.
    # The helper repairs only genuinely missing/rejected scan points.
    measurements, estimated_indices = complete_side_measurements(raw_scan)
    document = spatial_map_document(
        coordinates,
        args.mapping.as_posix(),
        measurement_coordinates=measurements,
        estimated_indices=estimated_indices,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(document, indent=2) + "\n", encoding="utf-8")
    panels = document["panels"]
    print(
        f"wrote={args.output} "
        + " ".join(
            f"{panel['name']}={panel['count']}led/{panel['width']}x{panel['height']}logical"
            for panel in panels
        )
        + f" measured={document['coordinate_quality']['measured']}"
        + f" estimated={document['coordinate_quality']['estimated']}"
    )


if __name__ == "__main__":
    main()
