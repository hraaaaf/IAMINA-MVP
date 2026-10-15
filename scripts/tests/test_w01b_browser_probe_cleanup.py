"""Regression: a passed browser proof must not fail during Chrome teardown."""
from __future__ import annotations

import subprocess
import sys
import unittest
from pathlib import Path
from unittest.mock import Mock, call, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from w01b_browser_api_pg_probe import _stop_chrome  # noqa: E402


class ChromeShutdownTest(unittest.TestCase):
    def test_already_exited_is_harmless(self):
        process = Mock()
        process.poll.return_value = 0
        with patch("w01b_browser_api_pg_probe.os.killpg") as kill_group:
            _stop_chrome(process)
        kill_group.assert_not_called()
        process.wait.assert_not_called()

    def test_running_browser_terminates_dedicated_group(self):
        process = Mock()
        process.pid = 123
        process.poll.return_value = None
        with patch("w01b_browser_api_pg_probe.os.killpg") as kill_group:
            _stop_chrome(process)
        kill_group.assert_called_once()
        process.wait.assert_called_once_with(timeout=5)

    def test_already_disappeared_process_group_is_harmless(self):
        process = Mock()
        process.pid = 123
        process.poll.return_value = None
        with patch(
            "w01b_browser_api_pg_probe.os.killpg",
            side_effect=ProcessLookupError(),
        ):
            _stop_chrome(process)
        process.wait.assert_not_called()

    def test_unresponsive_browser_group_is_force_stopped(self):
        process = Mock()
        process.pid = 123
        process.poll.return_value = None
        process.wait.side_effect = [
            subprocess.TimeoutExpired(cmd="chromium", timeout=5),
            0,
        ]
        with patch("w01b_browser_api_pg_probe.os.killpg") as kill_group:
            _stop_chrome(process)
        self.assertEqual(kill_group.call_count, 2)
        self.assertEqual(process.wait.call_args_list, [call(timeout=5), call(timeout=5)])


if __name__ == "__main__":
    unittest.main()
