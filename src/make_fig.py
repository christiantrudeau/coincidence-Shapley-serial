"""Figure: largest Shapley-serial gap relative to the average share, against mean job length / k.
n = 20, pooled over the three length distributions (900 problems per point)."""
import pandas as pd, numpy as np, matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

df = pd.read_csv("grid_results.csv")
d = df[df.n == 20]
g = d.groupby(["k", "rho_target"]).agg(x=("mean_len_over_k", "mean"),
                                       med=("gmax", "median"),
                                       p95=("gmax", lambda s: s.quantile(.95))).reset_index()
g.to_csv("fig_data.csv", index=False)

# ordinal colour ramp, with distinct markers for grayscale print
ramp = {2: "#86b6ef", 4: "#3987e5", 8: "#1c5cab", 16: "#0d366b"}
mk = {2: "o", 4: "s", 8: "^", 16: "D"}
ink, ink2, grid = "#0b0b0b", "#52514e", "#e4e3df"

plt.rcParams.update({"font.family": "serif", "mathtext.fontset": "cm", "pdf.fonttype": 42, "font.size": 9, "axes.edgecolor": ink2,
                     "axes.labelcolor": ink, "xtick.color": ink2, "ytick.color": ink2})
fig, ax = plt.subplots(figsize=(5.6, 3.5))
for k in [2, 4, 8, 16]:
    s = g[g.k == k].sort_values("x")
    ax.plot(s.x, 100 * s.med, color=ramp[k], lw=1.6, marker=mk[k], ms=5, mec="white", mew=1.0,
            solid_capstyle="round", zorder=3)
    ax.plot(s.x, 100 * s.p95, color=ramp[k], lw=1.0, ls=(0, (4, 2)), marker=mk[k], ms=3.5,
            mec="white", mew=0.6, zorder=2)
ax.set_xscale("log"); ax.set_yscale("log")
ax.set_xticks([0.5, 1, 2, 5, 10, 20]); ax.set_xticklabels(["0.5", "1", "2", "5", "10", "20"])
ax.set_yticks([0.5, 1, 2, 5, 10, 20]); ax.set_yticklabels(["0.5", "1", "2", "5", "10", "20"]); ax.set_ylim(0.3, 35)
ax.minorticks_off()
ax.set_xlabel("Mean job length divided by $k$ (periods of full capacity)")
ax.set_ylabel("Largest difference, % of average share")
ax.grid(True, color=grid, lw=0.6, zorder=0)
for sp in ["top", "right"]:
    ax.spines[sp].set_visible(False)
h1 = [Line2D([], [], color=ramp[k], marker=mk[k], lw=1.6, ms=5, mec="white", label=f"$k={k}$") for k in [2, 4, 8, 16]]
h2 = [Line2D([], [], color=ink2, lw=1.6, label="median"),
      Line2D([], [], color=ink2, lw=1.0, ls=(0, (4, 2)), label="95th percentile")]
l1 = ax.legend(handles=h1, loc="upper right", frameon=False, fontsize=8.5, labelcolor=ink)
ax.add_artist(l1)
ax.legend(handles=h2, loc="lower left", frameon=False, fontsize=8.5, labelcolor=ink)
fig.tight_layout()
fig.savefig("fig_gap.pdf"); fig.savefig("fig_gap.png", dpi=200)
print(g.round(4).to_string())
