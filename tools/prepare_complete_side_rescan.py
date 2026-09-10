"""Generate the complete 3,744-point mapping and audit report."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from pixelblaze_mapper.complete_side_rescan import rebuild_complete_side_mapping
from pixelblaze_mapper.lower_side_rewire import load_coordinate_array


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--current", type=Path, required=True)
    parser.add_argument("--scan", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()
    current = load_coordinate_array(args.current)
    scan = load_coordinate_array(args.scan)
    combined, report = rebuild_complete_side_mapping(current, scan)
    args.output.write_text(json.dumps(combined, indent=2) + "\n", encoding="utf-8")
    audit = report.to_dict()
    audit.update({
        "source_file": str(args.scan),
        "previous_mapping": str(args.current),
        "output_file": str(args.output),
        "network_outputs_enabled": False,
    })
    args.report.write_text(json.dumps(audit, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(audit, indent=2))


if __name__ == "__main__":
    main()
