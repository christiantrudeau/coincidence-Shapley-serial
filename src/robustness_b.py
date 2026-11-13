"""Robustness check B: small changes in length.

Start from problems where every length is a multiple of k, so that the optimistic Shapley value and the
serial rule coincide. Then change m of the lengths by one unit, all up, all down, or alternating up and
down ("mixed", m >= 2), and measure the gap between the two rules.

Design (paired): for each (n, k, rho, dist, rep) one base problem is drawn with the main study's length
distributions, rounded to multiples of k: l_i = k * max(1, rint(rho * x_i)). A random order of the agents
is drawn once; the first m agents in that order are the ones changed, so the changed sets are nested
(m = 1 is inside m = 2, and so on) and every m is compared on the same base problem.

Writes robustness_b.csv in the current folder.
Usage: python robustness_b.py [--processes P]      (default: all logical processors)
"""
import os, sys, time, zlib
from multiprocessing import Pool
import numpy as np, pandas as pd
from shapdp import shapley_opt_div, serial_div, grand_cost
from run_grid import draw_x

NS = [5, 10, 20, 50, 100]
KS = [2, 4, 8, 16]
RHOS = [0.5, 1, 2, 5, 10, 20]
DISTS = ["uniform", "heavy", "bimodal"]
REPS = {5: 50, 10: 50, 20: 50, 50: 20, 100: 10}
TOL = 1e-9
MIXED = 0          # value of the sign column for alternating changes


def m_levels(n):
    return sorted({m for m in (0, 1, 2, 3, 5, 10, round(n / 4), round(n / 2), n) if m <= n})


def base_problem(n, k, rho, dist, rep):
    """Lengths, all multiples of k, and the order in which agents are changed. rho is formatted with
    :g so that 1 and 1.0 (as read back from the CSV) give the same seed."""
    rng = np.random.default_rng(zlib.crc32(f"B-{n}-{k}-{rho:g}-{dist}-{rep}".encode()))
    q = np.maximum(1, np.rint(rho * draw_x(dist, n, rng))).astype(int)
    order = rng.permutation(n)
    return (k * q).tolist(), order.tolist()


def changed_lengths(base, order, m, sign):
    l = list(base)
    for j, i in enumerate(order[:m]):
        l[i] += sign if sign != MIXED else (1 if j % 2 == 0 else -1)
    return l


def one(args):
    n, k, rho, dist, rep = args
    base, order = base_problem(n, k, rho, dist, rep)
    rank = {i: r for r, i in enumerate(sorted(range(n), key=lambda i: (base[i], i)))}
    rows = []
    for m in m_levels(n):
        for sign in ((+1,) if m == 0 else (+1, -1) if m == 1 else (+1, -1, MIXED)):
            l = changed_lengths(base, order, m, sign)
            changed = order[:m]
            sh, se = shapley_opt_div(l, k), serial_div(l, k)
            d = sh - se
            ad = np.abs(d)
            CN = grand_cost(l, k)
            A = CN / n
            mask = np.zeros(n, bool); mask[changed] = True
            rows.append(dict(
                n=n, k=k, rho_target=rho, dist=dist, rep=rep, m=m, sign=sign,
                frac_changed=m / n,
                first_rank=(rank[order[0]] / (n - 1)) if m > 0 else np.nan,   # 0 shortest, 1 longest job
                n_remainders=len({x % k for x in l}),
                mean_len_over_k=float(np.mean(l)) / k,
                any_diff=bool(ad.max() > TOL),
                n_affected=int((ad > TOL).sum()),
                gmax=float(ad.max() / A),                              # share of the average share
                gabs=float(ad.max()),                                  # in periods (w0 = 1)
                gap_over_bound=float(ad.max() / (n * (k - 1) / k)),    # share of Proposition 2's bound
                realloc=float(0.5 * ad.sum() / CN),
                gmax_changed=float(ad[mask].max() / A) if m > 0 else 0.0,
                gmax_unchanged=float(ad[~mask].max() / A) if m < n else 0.0,
                d_changed_mean=float(d[mask].mean() / A) if m > 0 else 0.0,   # + : Shapley charges more
                efficiency_err=float(abs(sh.sum() - CN) + abs(se.sum() - CN)),
            ))
    return rows


def tasks():
    return [(n, k, rho, dist, rep) for n in NS for k in KS for rho in RHOS for dist in DISTS
            for rep in range(REPS[n])]


if __name__ == "__main__":
    procs = int(sys.argv[sys.argv.index("--processes") + 1]) if "--processes" in sys.argv else os.cpu_count()
    T = sorted(tasks(), key=lambda t: -t[0])          # largest problems first, for load balance
    t0 = time.time()
    with Pool(procs) as p:
        out = p.map(one, T, chunksize=1)
    df = pd.DataFrame([r for rows in out for r in rows])
    df = df.sort_values(["n", "k", "rho_target", "dist", "rep", "m", "sign"],
                        ascending=[True, True, True, True, True, True, False])
    df.to_csv("robustness_b.csv", index=False, lineterminator="\n")
    print(len(T), "base problems,", len(df), "rows in", round(time.time() - t0), "s")
