"""Tests of the numerical code. Run from the repository folder:  python -m unittest discover -s tests
Uses the same problems and seeds as run_grid.py. Reported failures mean the code changed behaviour."""
import random
import sys
import unittest
import zlib
from fractions import Fraction
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from run_grid import draw_x, NS, KS, RHOS, DISTS
from shapdp import shapley_opt_div, serial_div, grand_cost
from shapdp_exact import (shapley_opt_div_exact, serial_div_exact, grand_cost_exact,
                          brute_shapley_exact)

TOL = 1e-9          # the threshold of run_grid.py for "the two rules differ"


def lengths(n, k, rho, dist, rep):
    rng = np.random.default_rng(zlib.crc32(f"{n}-{k}-{rho}-{dist}-{rep}".encode()))
    return np.maximum(1, np.rint(k * rho * draw_x(dist, n, rng))).astype(int).tolist()


class ExactArithmetic(unittest.TestCase):
    def test_exact_dp_equals_exact_brute_force(self):
        rng = random.Random(1)
        for _ in range(100):
            n = rng.randint(1, 8)
            k = rng.choice([1, 2, 3, 4, 5, 8, 16])
            l = [rng.randint(1, 3 * k + 2) for _ in range(n)]
            self.assertEqual(shapley_opt_div_exact(l, k), brute_shapley_exact(l, k), (l, k))

    def test_running_example(self):
        self.assertEqual(shapley_opt_div_exact([2, 3, 6], 2), [2, Fraction(7, 2), Fraction(9, 2)])
        self.assertEqual(serial_div_exact([2, 3, 6], 2), [2, 3, 5])

    def test_float_code_matches_exact_values_on_grid_problems(self):
        # one problem per (n, k, dist) at rho = 0.5 and 5, up to n = 50; audit_full_grid.py covers n = 100
        for n in [5, 10, 20, 50]:
            for k in KS:
                for rho in [0.5, 5]:
                    for dist in DISTS:
                        l = lengths(n, k, rho, dist, 0)
                        she, see = shapley_opt_div_exact(l, k), serial_div_exact(l, k)
                        shf, sef = shapley_opt_div(l, k), serial_div(l, k)
                        err = max(abs(float(a) - b) for a, b in zip(she + see, list(shf) + list(sef)))
                        self.assertLess(err, 1e-11, (n, k, rho, dist))
                        same = she == see
                        self.assertEqual(same, float(np.max(np.abs(shf - sef))) <= TOL, (n, k, rho, dist))


class Efficiency(unittest.TestCase):
    def test_shares_sum_to_total_cost(self):
        for n in NS:
            for k in KS:
                for rho in RHOS:
                    for dist in DISTS:
                        l = lengths(n, k, rho, dist, 0)
                        CN = grand_cost(l, k)
                        self.assertLess(abs(shapley_opt_div(l, k).sum() - CN) / CN, 1e-12)
                        self.assertLess(abs(serial_div(l, k).sum() - CN) / CN, 1e-12)

    def test_exact_efficiency(self):
        for n, k in [(10, 4), (20, 8), (50, 16)]:
            l = lengths(n, k, 1, "heavy", 0)
            CN = grand_cost_exact(l, k)
            self.assertEqual(sum(shapley_opt_div_exact(l, k)), CN)
            self.assertEqual(sum(serial_div_exact(l, k)), CN)


class Coincidence(unittest.TestCase):
    def test_rules_coincide_when_lengths_are_multiples_of_k(self):
        rng = random.Random(2)
        for _ in range(100):
            n, k = rng.randint(2, 30), rng.choice([2, 3, 4, 8])
            l = [k * rng.randint(1, 6) for _ in range(n)]
            self.assertLess(np.max(np.abs(shapley_opt_div(l, k) - serial_div(l, k))), TOL)


class InputChecks(unittest.TestCase):
    def test_numpy_integers_give_the_same_answer_at_large_n(self):
        rng = np.random.default_rng(1)
        k = 16
        l = np.maximum(1, np.rint(k * 20 * rng.uniform(0, 2, 100))).astype(int)
        self.assertEqual(shapley_opt_div(l, k).tolist(), shapley_opt_div(l.tolist(), k).tolist())
        self.assertEqual(serial_div(l, k).tolist(), serial_div(l.tolist(), k).tolist())

    def test_lengths_outside_the_model_are_refused(self):
        for f in (shapley_opt_div, serial_div):
            for bad in ([0, 3, 6], [-1, 3, 6]):
                with self.assertRaises(ValueError):
                    f(bad, 2)
            for bad in ([2.5, 3, 6], [2.0, 3.0, 6.0]):
                with self.assertRaises(TypeError):
                    f(bad, 2)


if __name__ == "__main__":
    unittest.main()
