"""Run permanent MK2 acceptance + existing show regressions without physical USB.

Usage: python tools/check_mk2_acceptance.py [--json-report PATH]
Physical checks H1/H2 in docs/MK2_CONTROL_SPEC_DE.md remain separate.
"""
import argparse
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from pixelblaze_mapper.maschine_mk2 import dependencies
dependencies()
from pixelblaze_mapper.mk2_workflow import VERSION


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--json-report',type=Path)
    options = parser.parse_args()
    suite = unittest.TestSuite(unittest.TestLoader().discover(str(ROOT/'tests'),pattern)
                               for pattern in ('test_mk2*.py','test_show*.py','test_live_show_integration.py'))
    result = unittest.TextTestRunner(verbosity=1).run(suite)
    report = dict(version=VERSION,tests=result.testsRun,failures=len(result.failures),errors=len(result.errors),
                  skipped=len(result.skipped),software_passed=result.wasSuccessful(),
                  physical_acceptance='pending',specification='docs/MK2_CONTROL_SPEC_DE.md')
    if options.json_report:
        options.json_report.parent.mkdir(parents=True,exist_ok=True)
        options.json_report.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(report,ensure_ascii=False))
    return 0 if result.wasSuccessful() else 1


if __name__=='__main__':
    raise SystemExit(main())
