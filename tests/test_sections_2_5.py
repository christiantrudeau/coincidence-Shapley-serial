"""Runs every check of ejor_rr_checks.py (the numbers quoted in Sections 2-5)."""
import contextlib
import io
import random
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import ejor_rr_checks as checks


class Sections2to5(unittest.TestCase):
    def test_all_checks_pass(self):
        checks.RESULTS.clear()
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            checks.section_2()
            checks.section_3()
            checks.section_3_order()
            checks.random_checks(random.Random(2026))
        failed = [line for line in out.getvalue().splitlines() if line.startswith("[FAIL]")]
        self.assertEqual(failed, [])
        self.assertEqual(len(checks.RESULTS), 56)


if __name__ == "__main__":
    unittest.main()
