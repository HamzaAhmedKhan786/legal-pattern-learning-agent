from __future__ import annotations

import sys
import unittest
from pathlib import Path


BACKEND = Path(__file__).resolve().parents[1] / "web" / "backend"
SRC = Path(__file__).resolve().parents[1] / "src"
for path in (BACKEND, SRC):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from classifier_adapter import classifier_command_args  # noqa: E402


class BackendClassifierTest(unittest.TestCase):
    def test_classifier_command_accepts_json_array(self) -> None:
        command = '["python","adapter.py","--project-root","C:\\\\DocClassifier"]'

        self.assertEqual(classifier_command_args(command), ["python", "adapter.py", "--project-root", "C:\\DocClassifier"])


if __name__ == "__main__":
    unittest.main()
