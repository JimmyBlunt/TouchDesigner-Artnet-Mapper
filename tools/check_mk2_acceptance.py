"""Run permanent MK2 acceptance + existing show regressions without physical USB.

Usage: python tools/check_mk2_acceptance.py [--json-report PATH]
Physical checks H1/H2 in docs/MK2_CONTROL_SPEC_DE.md remain separate.
"""
import argparse
import json
from pathlib import Path
import sys
import unittest
from datetime import datetime, timezone
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from pixelblaze_mapper.maschine_mk2 import dependencies
dependencies()
from pixelblaze_mapper.mk2_workflow import VERSION


class AcceptanceResult(unittest.TextTestResult):
    """Retain individually reviewable results, including failed sub-scenarios."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.cases = []

    def startTest(self, test):
        self.started = time.perf_counter()
        self.case = dict(id=test.id(), status='passed')
        super().startTest(test)

    def addFailure(self, test, error):
        self.case['status'] = 'failed'
        super().addFailure(test, error)

    def addError(self, test, error):
        self.case['status'] = 'error'
        super().addError(test, error)

    def addSkip(self, test, reason):
        self.case.update(status='skipped', reason=reason)
        super().addSkip(test, reason)

    def addExpectedFailure(self, test, error):
        self.case['status'] = 'expected_failure'
        super().addExpectedFailure(test, error)

    def addUnexpectedSuccess(self, test):
        self.case['status'] = 'unexpected_success'
        super().addUnexpectedSuccess(test)

    def addSubTest(self, test, subtest, error):
        if error:
            self.case['status'] = 'failed'
            self.case.setdefault('failed_scenarios', []).append(str(subtest))
        super().addSubTest(test, subtest, error)

    def stopTest(self, test):
        self.case['seconds'] = round(time.perf_counter()-self.started, 4)
        self.cases.append(self.case)
        super().stopTest(test)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--json-report',type=Path)
    options = parser.parse_args()
    suite = unittest.TestSuite(unittest.TestLoader().discover(str(ROOT/'tests'),pattern)
                               for pattern in ('test_mk2*.py','test_show*.py','test_live_show_integration.py'))
    result = unittest.TextTestRunner(verbosity=1, resultclass=AcceptanceResult).run(suite)
    report = dict(version=VERSION,tests=result.testsRun,failures=len(result.failures),errors=len(result.errors),
                  skipped=len(result.skipped),expected_failures=len(result.expectedFailures),
                  software_passed=result.wasSuccessful() and not result.skipped and not result.expectedFailures,
                  physical_acceptance='pending',specification='docs/MK2_CONTROL_SPEC_DE.md')
    if options.json_report:
        options.json_report.parent.mkdir(parents=True,exist_ok=True)
        detailed = dict(report, finished_at=datetime.now(timezone.utc).isoformat(), cases=result.cases)
        options.json_report.write_text(json.dumps(detailed,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(report,ensure_ascii=False))
    return 0 if report['software_passed'] else 1


if __name__=='__main__':
    raise SystemExit(main())
