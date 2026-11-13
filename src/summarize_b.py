"""Summaries of robustness check B, computed from robustness_b.csv in the current folder.
Writes robustness_b_summary.json (key figures) and robustness_b_tables.md (all tables)."""
import json
import numpy as np, pandas as pd

df = pd.read_csv("robustness_b.csv")
df["dir"] = df.sign.map({1: "up", -1: "down", 0: "mixed"})
ch = df[df.m > 0].copy()
ch["m_label"] = np.where(ch.m == ch.n, "all", ch.m.astype(str))
one = ch[ch.m == 1].assign(longest=lambda x: x.first_rank == 1.0)
M_ORDER = ["1", "2", "3", "5", "10", "12", "25", "50", "all"]
pct = lambda v: "" if pd.isna(v) else f"{100 * v:.1f}"
num = lambda v: "" if pd.isna(v) else f"{v:.2f}"
P = lambda x: round(100 * float(x), 1)


def md(t):
    if isinstance(t, pd.Series):
        t = t.to_frame()
    cols = [str(c) for c in t.columns]
    lines = ["| " + " | ".join([str(t.index.name or "")] + cols) + " |",
             "| " + " | ".join(["---"] * (len(cols) + 1)) + " |"]
    lines += ["| " + " | ".join([str(i)] + [str(v) for v in r]) + " |" for i, r in zip(t.index, t.values)]
    return "\n".join(lines)


def by_m_n(sub, value, fn, fmt):
    t = sub.groupby(["m_label", "n"])[value].agg(fn).unstack()
    return t.loc[[x for x in M_ORDER if x in t.index]].map(fmt)


tables = []
for d in ["up", "down", "mixed"]:
    tables.append((f"Share of problems where the rules differ (%), lengths changed {d}",
                   by_m_n(ch[ch.dir == d], "any_diff", "mean", pct)))
for d in ["up", "down", "mixed"]:
    tables.append((f"Median largest gap, % of the average share, lengths changed {d}",
                   by_m_n(ch[ch.dir == d], "gmax", "median", pct)))
    tables.append((f"95th percentile of the largest gap, % of the average share, lengths changed {d}",
                   by_m_n(ch[ch.dir == d], "gmax", lambda s: s.quantile(.95), pct)))
tables += [
    ("Median largest gap in periods (w0 = 1), all directions", by_m_n(ch, "gabs", "median", num)),
    ("Largest gap as a share of the bound of Proposition 2: maximum, all directions",
     by_m_n(ch, "gap_over_bound", "max", lambda v: "" if pd.isna(v) else f"{v:.3f}")),
    ("One length changed: median largest gap (% of the average share), by rho (rows) and n",
     one.groupby(["rho_target", "n"]).gmax.median().unstack().map(pct)),
    ("One length changed: median largest gap of the changed agent and of the others (% of the average share)",
     one.groupby("n")[["gmax_changed", "gmax_unchanged"]].median().map(pct)),
    ("One length changed: share of problems where the rules differ (%), by whether the changed job is the longest",
     one.groupby(["longest", "dir"]).any_diff.mean().map(pct).unstack()),
    ("One length changed: Shapley value minus serial rule for the changed agent, mean (% of the average share)",
     one.groupby(["n", "dir"]).d_changed_mean.mean().map(pct).unstack()),
    ("One length changed: median number of agents with a gap", one.groupby("n").n_affected.median()),
]
with open("robustness_b_tables.md", "w", encoding="utf-8", newline="\n") as f:
    f.write("# Robustness check B: tables\n\nComputed by `src/summarize_b.py` from `robustness_b.csv`. "
            "Rows: number of lengths changed (m); columns: number of agents (n).\n")
    for title, t in tables:
        f.write(f"\n## {title}\n\n{md(t)}\n")

S = {
    "base_problems": int((df.m == 0).sum()),
    "rows": int(len(df)),
    "unchanged_problems_where_rules_differ": int(df[df.m == 0].any_diff.sum()),
    "rows_with_one_remainder": int((df.n_remainders == 1).sum()),
    "rows_with_one_remainder_where_rules_differ": int(df[df.n_remainders == 1].any_diff.sum()),
    "max_efficiency_error": float(f"{df.efficiency_err.max():.1e}"),
    "smallest_nonzero_gap_periods": round(float(df.gabs[df.any_diff].min()), 4),
    "one_change_differ_pct_by_n": {int(n): P(v) for n, v in one.groupby("n").any_diff.mean().items()},
    "one_change_median_gap_pct_by_n": {int(n): P(v) for n, v in one.groupby("n").gmax.median().items()},
    "max_gap_over_bound": round(float(ch.gap_over_bound.max()), 3),
}
with open("robustness_b_summary.json", "w", newline="\n") as f:
    json.dump(S, f, indent=1)
    f.write("\n")
for key, value in S.items():
    print(key, value)
