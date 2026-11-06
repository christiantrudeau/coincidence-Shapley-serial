"""Every number quoted in Section 6 (numerical study) and Table 3, computed from grid_results.csv."""
import pandas as pd, numpy as np, json
df = pd.read_csv("grid_results.csv")
P = lambda x: round(100 * float(x), 1)
S = {}
S["instances"] = len(df)
S["differ_all_pct"] = P(df.any_diff.mean())
S["differ_n_ge_20_min_cell_pct"] = P(df[df.n >= 20].groupby(["n", "rho_target"]).any_diff.mean().min())
S["coincide_share_with_n_le_10_pct"] = P((df[~df.any_diff].n <= 10).mean())
S["median_gmax_n20_by_rho_pct"] = {r: P(v) for r, v in df[df.n == 20].groupby("rho_target").gmax.median().items()}
S["median_gmax_n20_rho05_by_k_pct"] = {k: P(v) for k, v in df[(df.n == 20) & (df.rho_target == 0.5)].groupby("k").gmax.median().items()}
S["median_gmax_n20_rho5_by_k_pct"] = {k: P(v) for k, v in df[(df.n == 20) & (df.rho_target == 5)].groupby("k").gmax.median().items()}
S["median_gmax_by_dist_rho05_n20_pct"] = {d: P(v) for d, v in df[(df.n == 20) & (df.rho_target == 0.5)].groupby("dist").gmax.median().items()}
S["max_gmax_all_pct"] = P(df.gmax.max())
S["max_gmax_by_n_pct"] = {n: P(v) for n, v in df.groupby("n").gmax.max().items()}
S["realloc_median_n20_by_rho_pct"] = {r: round(100 * v, 2) for r, v in df[df.n == 20].groupby("rho_target").realloc.median().items()}
S["realloc_max_all_pct"] = P(df.realloc.max())
S["transfer_ratio_median_n20_by_rho_pct"] = {r: P(v) for r, v in df[df.n == 20].groupby("rho_target").g_transfer.median().items()}
S["agent_rel_median_n20_by_rho_pct"] = {r: P(v) for r, v in df[df.n == 20].groupby("rho_target").g_agent.median().items()}
S["short_more_pct"] = P((df.d_short > 1e-9).mean()); S["short_less_pct"] = P((df.d_short < -1e-9).mean())
S["long_less_pct"] = P((df.d_long < -1e-9).mean()); S["long_more_pct"] = P((df.d_long > 1e-9).mean())
S["max_gap_over_bound_n(k-1)/k_by_n"] = {n: round(2 * v, 3) for n, v in df.groupby("n").g_bound.max().items()}
S["bound_violations"] = int((2 * df.g_bound > 1 + 1e-9).sum())
S["rel_bound_violations"] = int((df.gmax > 2 * (df.k - 1) / df.min_len + 1e-9).sum())
S["realized_mean_len_over_k_by_rho"] = {r: round(v, 2) for r, v in df.groupby("rho_target").mean_len_over_k.mean().items()}

df["absgap"] = df.g_bound * 2 * df.n * (df.k - 1) / df.k   # max_i |d_i| in units of w0
S["abs_median_all"] = round(df.absgap.median(), 2)
S["abs_p95_all"] = round(df.absgap.quantile(.95), 2)
S["abs_share_below_w0_pct"] = P((df.absgap < 1).mean())
S["abs_max_all"] = round(df.absgap.max(), 2)
S["abs_median_by_n"] = {n: round(v, 2) for n, v in df.groupby("n").absgap.median().items()}
import zlib
from run_grid import draw_x
z = df[~df.any_diff]; maj = 0
for r in z.itertuples():
    rng = np.random.default_rng(zlib.crc32(f"{r.n}-{r.k}-{r.rho_target}-{r.dist}-{r.rep}".encode()))
    l = np.maximum(1, np.rint(r.k * r.rho_target * draw_x(r.dist, r.n, rng))).astype(int)
    maj += np.bincount(l).max() > r.n / 2
S["coincide_majority_same_length_pct"] = P(maj / len(z))
json.dump(S, open("summary.json", "w"), indent=1)
for a, b in S.items(): print(a, b)

# Table 3: median (95th percentile) of the largest gap, % of the average share; last column max over all n
med = df.groupby(["rho_target", "n"]).gmax.median().unstack() * 100
p95 = df.groupby(["rho_target", "n"]).gmax.quantile(.95).unstack() * 100
mx = df.groupby("rho_target").gmax.max() * 100
lines = []
for r in med.index:
    cells = [f"{med.loc[r, n]:.1f} ({p95.loc[r, n]:.1f})" for n in med.columns]
    lab = f"{r:g}"
    lines.append(f"{lab} & " + " & ".join(cells) + f" & {mx.loc[r]:.1f} \\\\")
open("table3_rows.tex", "w").write("\n".join(lines) + "\n")
print("\n".join(lines))
