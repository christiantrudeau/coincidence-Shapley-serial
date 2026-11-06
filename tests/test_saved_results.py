"""Links the saved outputs to the code: the numbers reported in Section 6 are rebuilt from the saved
data, and a sample of problems is recomputed from its seeds and compared with the saved data."""
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "tests"))
from compare_results import TOL, compare_searches, compare_summary
from run_grid import one, KS, RHOS, DISTS


class SavedResults(unittest.TestCase):
    def test_section_6_numbers_rebuild_from_saved_data(self):
        with tempfile.TemporaryDirectory() as folder:
            shutil.copy(ROOT / "data" / "grid_results.csv", folder)
            for script in ("summarize.py", "make_fig.py"):
                subprocess.run([sys.executable, str(ROOT / "src" / script)], cwd=folder, check=True,
                               capture_output=True)
            self.assertEqual(compare_summary(Path(folder)), [])

    def test_sample_of_problems_recomputes_from_seeds(self):
        keys = ["n", "k", "rho_target", "dist", "rep"]
        tasks = [(n, k, r, d, 0) for n in (5, 10, 20) for k in KS for r in RHOS for d in DISTS]
        fresh = pd.DataFrame([one(t) for t in tasks])
        saved = pd.read_csv(ROOT / "data" / "grid_results.csv")
        both = fresh.merge(saved, on=keys, suffixes=("", "_saved"))
        self.assertEqual(len(both), 216)
        self.assertTrue((both.any_diff == both.any_diff_saved).all())
        for column in fresh.columns:
            if column not in keys and column != "any_diff":
                self.assertLessEqual(float((both[column] - both[column + "_saved"]).abs().max()), TOL, column)


class SearchCheck(unittest.TestCase):
    """A search row may differ from the saved files, but it may not break the statement of the paper."""

    def check(self, gap_over_bound):
        with tempfile.TemporaryDirectory() as folder:
            folder = Path(folder)
            shutil.copy(ROOT / "results" / "adv_results.json", folder)
            rows = json.loads((ROOT / "results" / "adv2_results.json").read_text())
            rows[0]["gap_over_bound"] = gap_over_bound
            (folder / "adv2_results.json").write_text(json.dumps(rows))
            return compare_searches(folder)

    def test_different_row_within_half_of_the_bound_passes(self):
        failures, rows_differ, largest = self.check(0.49)
        self.assertEqual((failures, rows_differ), ([], 1))
        self.assertLessEqual(largest, 0.5 + TOL)

    def test_row_above_half_of_the_bound_fails(self):
        failures, _, largest = self.check(0.51)
        self.assertEqual(len(failures), 1)
        self.assertGreater(largest, 0.5)


if __name__ == "__main__":
    unittest.main()
