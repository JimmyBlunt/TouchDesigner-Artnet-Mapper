"""No networking: test admission and cleanup around the physical sender boundary."""
import contextlib
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock, patch

from pixelblaze_mapper import gico_camera_benchmark as bench
from tools import gico_camera_test as tool


class SenderBoundaryTests(unittest.TestCase):
    def test_failed_td_off_check_never_constructs_worker(self):
        factory = Mock()
        with tempfile.TemporaryDirectory() as directory:
            with patch.object(tool, "assert_td_off", side_effect=RuntimeError("TD live")):
                with self.assertRaisesRegex(RuntimeError, "TD live"):
                    tool.run(Path(directory), bench.plan(), factory)
        factory.assert_not_called()

    def test_submission_failure_still_closes_worker_and_records_error(self):
        sender = Mock()
        sender.submit.side_effect = [True, RuntimeError("synthetic submission failure")]
        sender.close.return_value = {"running": False, "blackout_packets": 48}
        factory = Mock(return_value=sender)
        with tempfile.TemporaryDirectory() as directory:
            with patch.object(tool, "assert_td_off"), contextlib.redirect_stdout(io.StringIO()):
                with self.assertRaisesRegex(RuntimeError, "synthetic submission"):
                    tool.run(Path(directory), bench.plan(), factory)
            result = json.loads((Path(directory) / "run.json").read_text())
            self.assertFalse(result["complete"])
            self.assertIn("synthetic submission failure", result["error"])
            self.assertEqual(result["worker_final"]["blackout_packets"], 48)
            sender.close.assert_called_once()
            self.assertEqual(sender.submit.call_count, 2)
            for call in sender.submit.call_args_list:
                batch = call.args[0]
                self.assertEqual(len(batch), 24)
                self.assertTrue(all(target == ("10.0.0.244", 6454) for _, target in batch))
                self.assertTrue(all(packet[12] == 0 for packet, _ in batch))
            logged = [json.loads(line) for line in (Path(directory) / "submitted-frames.jsonl").read_text().splitlines()]
            self.assertEqual(logged[0]["sequence"], 0)


if __name__ == "__main__":
    unittest.main()
