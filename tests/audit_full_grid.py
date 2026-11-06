"""Full-grid audits (same problems and seeds as run_grid.py); slower than test_numerical.py.
  python tests/audit_full_grid.py efficiency   all 78,480 problems, the code in src/:
                                      do the shares add up to C(N)? how close to 1e-9 are
                                      the smallest differences flagged as "differ"?
  python tests/audit_full_grid.py exact        sample (reps 0-2 of every cell = 1,080 problems):
                                      exact-fraction Shapley and serial vs the float code."""
import sys, zlib, json, time
from pathlib import Path
import numpy as np
from multiprocessing import Pool
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
from run_grid import draw_x, NS, KS, RHOS, DISTS, REPS
from shapdp import shapley_opt_div, serial_div, grand_cost
from shapdp_exact import shapley_opt_div_exact, serial_div_exact, grand_cost_exact

TOL = 1e-9   # threshold used by run_grid.py for any_diff


def lengths(n, k, rho, dist, rep):
    rng = np.random.default_rng(zlib.crc32(f"{n}-{k}-{rho}-{dist}-{rep}".encode()))
    return np.maximum(1, np.rint(k * rho * draw_x(dist, n, rng))).astype(int).tolist()


def eff(args):
    l = lengths(*args)
    k = args[1]
    sh = shapley_opt_div(l, k); se = serial_div(l, k); CN = grand_cost(l, k)
    return dict(n=args[0], k=k, rho=args[2], dist=args[3], rep=args[4], CN=CN,
                eff_sh=abs(sh.sum() - CN) / CN, eff_se=abs(se.sum() - CN) / CN,
                maxd=float(np.max(np.abs(sh - se))))


def exact(args):
    l = lengths(*args)
    k = args[1]
    t = time.time()
    she = shapley_opt_div_exact(l, k); see = serial_div_exact(l, k); CN = grand_cost_exact(l, k)
    shf = shapley_opt_div(l, k); sef = serial_div(l, k)
    de = [a - b for a, b in zip(she, see)]
    maxd_exact = max(abs(x) for x in de)
    maxd_float = float(np.max(np.abs(shf - sef)))
    return dict(n=args[0], k=k, rho=args[2], dist=args[3], rep=args[4],
                err_sh=max(abs(float(a) - b) for a, b in zip(she, shf)),
                err_se=max(abs(float(a) - b) for a, b in zip(see, sef)),
                err_d=max(abs(float(a) - (b - c)) for a, b, c in zip(de, shf, sef)),
                eff_exact=(sum(she) == CN and sum(see) == CN),
                differ_exact=maxd_exact != 0, differ_float=maxd_float > TOL,
                maxd_exact=float(maxd_exact), secs=time.time() - t)


if __name__ == "__main__":
    mode = sys.argv[1]
    t0 = time.time()
    if mode == "efficiency":
        tasks = [(n, k, r, d, rep) for n in NS for k in KS for r in RHOS for d in DISTS for rep in range(REPS[n])]
        with Pool(10) as p:
            rows = p.map(eff, tasks, chunksize=20)
        diff = [r["maxd"] for r in rows if r["maxd"] > TOL]
        gray = [r for r in rows if 1e-13 < r["maxd"] <= 1e-6]
        out = dict(problems=len(rows),
                   max_rel_eff_error_shapley=max(r["eff_sh"] for r in rows),
                   max_rel_eff_error_serial=max(r["eff_se"] for r in rows),
                   max_abs_eff_error_shapley=max(r["eff_sh"] * r["CN"] for r in rows),
                   flagged_differ=len(diff),
                   smallest_flagged_gap=min(diff),
                   largest_unflagged_gap=max((r["maxd"] for r in rows if r["maxd"] <= TOL), default=0.0),
                   gray_zone_gaps_1e13_to_1e6=len(gray),
                   seconds=round(time.time() - t0))
    else:
        tasks = [(n, k, r, d, rep) for n in NS for k in KS for r in RHOS for d in DISTS for rep in range(3)]
        tasks.sort(key=lambda a: -a[0] * a[1])          # slowest first for better load balance
        with Pool(10) as p:
            rows = p.map(exact, tasks, chunksize=1)
        out = dict(problems=len(rows),
                   max_abs_error_shapley=max(r["err_sh"] for r in rows),
                   max_abs_error_serial=max(r["err_se"] for r in rows),
                   max_abs_error_difference=max(r["err_d"] for r in rows),
                   max_error_by_n={n: max(r["err_d"] for r in rows if r["n"] == n) for n in NS},
                   exact_efficiency_all=all(r["eff_exact"] for r in rows),
                   classification_agrees=sum(r["differ_exact"] == r["differ_float"] for r in rows),
                   exact_coincidences=sum(not r["differ_exact"] for r in rows),
                   smallest_nonzero_exact_gap=min(r["maxd_exact"] for r in rows if r["differ_exact"]),
                   seconds=round(time.time() - t0))
    json.dump(out, open(f"audit_{mode}.json", "w"), indent=1)
    for a, b in out.items():
        print(a, b)
