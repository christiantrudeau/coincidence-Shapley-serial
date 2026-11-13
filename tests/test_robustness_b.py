"""Robustness check B: the saved data recomputes from its seeds, its summary rebuilds, and the rules coincide
exactly whenever all lengths have the same remainder modulo k (docs/robustness_b.md)."""
import gzip
import json
import random
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
from robustness_b import one, base_problem, changed_lengths, KS, RHOS, DISTS, MIXED
from shapdp_exact import shapley_opt_div_exact, serial_div_exact

DATA = ROOT / "data" / "robustness_b.csv.gz"
TOL = 1e-9


class SavedData(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.saved = pd.read_csv(DATA)

    def test_sample_recomputes_from_seeds(self):
        keys = ["n", "k", "rho_target", "dist", "rep", "m", "sign"]
        tasks = [(n, k, r, d, 0) for n in (5, 10) for k in KS for r in RHOS for d in DISTS]
        fresh = pd.DataFrame([row for t in tasks for row in one(t)])
        both = fresh.merge(self.saved, on=keys, suffixes=("", "_saved"))
        self.assertEqual(len(both), len(fresh))
        self.assertTrue((both.any_diff == both.any_diff_saved).all())
        for column in ["gmax", "gabs", "gap_over_bound", "gmax_changed", "gmax_unchanged", "d_changed_mean"]:
            self.assertLessEqual(float((both[column] - both[column + "_saved"]).abs().max()), TOL, column)

    def test_sample_agrees_with_exact_arithmetic(self):
        sample = self.saved[(self.saved.n <= 10) & (self.saved.m > 0)].sample(60, random_state=3)
        for r in sample.itertuples():
            base, order = base_problem(r.n, r.k, r.rho_target, r.dist, r.rep)
            l = changed_lengths(base, order, r.m, r.sign)
            gap = max(abs(a - b) for a, b in zip(shapley_opt_div_exact(l, r.k), serial_div_exact(l, r.k)))
            self.assertEqual(gap != 0, bool(r.any_diff), r)
            self.assertLessEqual(abs(float(gap) - r.gabs), TOL, r)

    def test_unchanged_problems_coincide(self):
        self.assertFalse(self.saved[self.saved.m == 0].any_diff.any())

    def test_summary_rebuilds_from_saved_data(self):
        with tempfile.TemporaryDirectory() as folder:
            with gzip.open(DATA) as packed, open(Path(folder) / "robustness_b.csv", "wb") as plain:
                shutil.copyfileobj(packed, plain)
            subprocess.run([sys.executable, str(ROOT / "src" / "summarize_b.py")], cwd=folder, check=True,
                           capture_output=True)
            new = json.loads((Path(folder) / "robustness_b_summary.json").read_text())
            old = json.loads((ROOT / "results" / "robustness_b_summary.json").read_text())
            self.assertEqual(new, old)


class EqualRemainders(unittest.TestCase):
    def test_rules_coincide_when_all_lengths_share_a_remainder(self):
        rng = random.Random(7)
        for _ in range(60):
            n, k = rng.randint(2, 8), rng.choice([2, 3, 4, 5, 8])
            r = rng.randrange(k)
            l = [k * rng.randint(0 if r else 1, 4) + r for _ in range(n)]
            self.assertEqual(shapley_opt_div_exact(l, k), serial_div_exact(l, k), (l, k))

    def test_one_change_from_multiples_of_k_can_separate_the_rules(self):
        # Proposition 2's tightness example: l = (1, k, ..., k), here k = 2 and n = 4
        l = [1, 2, 2, 2]
        self.assertNotEqual(shapley_opt_div_exact(l, 2), serial_div_exact(l, 2))

    def test_mixed_changes_alternate(self):
        base, order = base_problem(10, 4, 1, "uniform", 0)
        l = changed_lengths(base, order, 3, MIXED)
        self.assertEqual([l[i] - base[i] for i in order[:3]], [1, -1, 1])


if __name__ == "__main__":
    unittest.main()
