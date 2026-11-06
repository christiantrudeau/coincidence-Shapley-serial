"""Numerical study: optimistic Shapley value vs serial rule, scheduling problems with
discretely divisible jobs.  Exact computation (shapdp.py).  Writes grid_results.csv."""
import numpy as np, pandas as pd, sys, time, zlib
from multiprocessing import Pool
from shapdp import shapley_opt_div, serial_div, grand_cost, completion_times

NS = [5, 10, 20, 50, 100]
KS = [2, 4, 8, 16]
RHOS = [0.5, 1, 2, 5, 10, 20]          # target mean job length, in periods (= mean l / k)
DISTS = ["uniform", "heavy", "bimodal"]
REPS = {5: 300, 10: 300, 20: 300, 50: 150, 100: 40}


def draw_x(dist, n, rng):
    if dist == "uniform":
        return rng.uniform(0, 2, n)
    if dist == "heavy":
        return rng.lognormal(-0.5, 1.0, n)          # mean 1
    small = rng.random(n) < 0.8
    return np.where(small, rng.uniform(0, 0.5, n), rng.uniform(2, 6, n))   # mean 1


def one(args):
    n, k, rho, dist, rep = args
    rng = np.random.default_rng(zlib.crc32(f"{n}-{k}-{rho}-{dist}-{rep}".encode()))
    l = np.maximum(1, np.rint(k * rho * draw_x(dist, n, rng))).astype(int).tolist()
    sh = shapley_opt_div(l, k)
    se = serial_div(l, k)
    C = completion_times(l, k)
    CN = grand_cost(l, k)
    d = sh - se
    A = CN / n
    t_ser = se - C
    T = np.abs(t_ser).sum()
    iL = int(np.argmax(l)); iS = int(np.argmin(l))
    return dict(n=n, k=k, rho_target=rho, dist=dist, rep=rep,
                mean_len_over_k=float(np.mean(l)) / k,
                min_len=int(min(l)), frac_nonmult=float(np.mean([x % k != 0 for x in l])),
                gmax=float(np.max(np.abs(d)) / A), gmean=float(np.mean(np.abs(d)) / A),
                g_agent=float(np.max(np.abs(d) / se)),
                # g_bound divides by 2n(k-1)/k, twice the bound w0 n(k-1)/k of Proposition 2:
                # the largest gap as a fraction of Proposition 2's bound is 2 * g_bound.
                g_bound=float(np.max(np.abs(d)) / (2 * n * (k - 1) / k)),
                realloc=float(0.5 * np.abs(d).sum() / CN),
                g_transfer=float(np.abs(d).sum() / T) if T > 1e-12 else np.nan,
                any_diff=bool(np.max(np.abs(d)) > 1e-9),
                d_long=float(d[iL] / A), d_short=float(d[iS] / A))


if __name__ == "__main__":
    tasks = [(n, k, rho, dist, rep) for n in NS for k in KS for rho in RHOS for dist in DISTS
             for rep in range(REPS[n])]
    t0 = time.time()
    with Pool(2) as p:
        rows = p.map(one, tasks, chunksize=20)
    df = pd.DataFrame(rows)
    df.to_csv("grid_results.csv", index=False, lineterminator="\n")
    print(len(df), "instances in", round(time.time() - t0), "s")
