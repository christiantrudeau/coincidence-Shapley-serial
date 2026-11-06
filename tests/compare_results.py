"""Compare a fresh run with the saved study (data/grid_results.csv and results/).
Usage: python tests/compare_results.py [folder of the fresh run, default outputs]
Exits with an error if any reported value differs.

Numbers that the paper reports (summary.json, Table 3) must be equal. Unrounded values may differ
by floating-point noise across machines, so they are compared with a tolerance of TOL.

The hill-climbing searches are checked differently. They stop wherever their route ends, and the last
digits of a number can change the route (docs/machine_and_run_times.md). So what must hold on every
system is the statement of the paper, that no gap found exceeds half of the bound; rows that differ
from the saved files are counted and reported, but they are not an error."""
import json
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
TOL = 1e-9          # the threshold of run_grid.py for "the two rules differ"
GRID_EXACT = ["n", "k", "rho_target", "dist", "rep", "min_len", "any_diff"]
SEARCHES = (("adv_results.json", "m_g_bound", 0.25),    # g_bound = 0.25 is half of the bound
            ("adv2_results.json", "gap_over_bound", 0.5))


def walk(a, b, path=""):
    """Differences between two nested values; floats are compared with TOL."""
    if isinstance(a, dict) and isinstance(b, dict):
        out = []
        for key in sorted(set(a) | set(b)):
            if key not in a or key not in b:
                out.append((f"{path}/{key}", a.get(key, "<absent>"), b.get(key, "<absent>")))
            else:
                out += walk(a[key], b[key], f"{path}/{key}")
        return out
    if isinstance(a, list) and isinstance(b, list):
        if len(a) != len(b):
            return [(path, f"{len(a)} items", f"{len(b)} items")]
        return [d for i, (x, y) in enumerate(zip(a, b)) for d in walk(x, y, f"{path}[{i}]")]
    if isinstance(a, float) or isinstance(b, float):
        return [] if abs(a - b) <= TOL else [(path, a, b)]
    return [] if a == b else [(path, a, b)]


def compare_grid(new_csv, ref_csv=ROOT / "data" / "grid_results.csv"):
    """Returns (problems compared, largest difference, design and flags equal, same bytes)."""
    new, ref = pd.read_csv(new_csv), pd.read_csv(ref_csv)
    if len(new) != len(ref) or list(new.columns) != list(ref.columns):
        return len(new), float("inf"), False, False
    exact = all((new[c] == ref[c]).all() for c in GRID_EXACT)
    floats = [c for c in ref.columns if c not in GRID_EXACT]
    worst = max(float((new[c] - ref[c]).abs().max()) for c in floats)
    nan_same = all((new[c].isna() == ref[c].isna()).all() for c in floats)
    same_bytes = (Path(new_csv).read_bytes().replace(b"\r\n", b"\n")
                  == Path(ref_csv).read_bytes().replace(b"\r\n", b"\n"))
    return len(ref), worst, exact and nan_same, same_bytes


def compare_summary(new):
    """Differences in the numbers of Section 6, Table 3 and the data of Figure 1."""
    res = ROOT / "results"
    out = walk(json.loads((new / "summary.json").read_text()),
               json.loads((res / "summary.json").read_text()), "summary.json")
    if (new / "table3_rows.tex").read_text().split() != (res / "table3_rows.tex").read_text().split():
        out.append(("table3_rows.tex", "differs", ""))
    a, b = pd.read_csv(new / "fig_data.csv"), pd.read_csv(res / "fig_data.csv")
    if len(a) != len(b) or float((a[["x", "med", "p95"]] - b[["x", "med", "p95"]]).abs().max().max()) > TOL:
        out.append(("fig_data.csv", "differs", ""))
    return out


def compare_searches(new):
    """Checks the two hill-climbing searches.
    Returns (failures, rows that differ from the saved files, largest gap as a share of the bound)."""
    out, rows_differ, largest = [], 0, 0.0
    for name, measure, half_bound in SEARCHES:
        fresh = json.loads((new / name).read_text())
        saved = json.loads((ROOT / "results" / name).read_text())
        design = [[(row.get("obj"), row["k"], row["n"]) for row in rows] for rows in (fresh, saved)]
        if design[0] != design[1]:
            out.append((name, "different rows", "same objectives, k and n expected"))
            continue
        rows_differ += sum(1 for a, b in zip(fresh, saved) if walk(a, b))
        for i, row in enumerate(fresh):
            largest = max(largest, row[measure] / (2 * half_bound))
            if row[measure] > half_bound + TOL:
                out.append((f"{name}[{i}]/{measure}", row[measure], f"above half of the bound, {half_bound}"))
    return out, rows_differ, largest


def compare_pilot(new):
    """Differences in the pilot table. The run times at the end of the file are left out."""
    def table(folder):
        lines = (folder / "pilot_output.txt").read_text().splitlines()
        return [line.rstrip() for line in lines if not line.startswith("n=")]
    return [] if table(new) == table(ROOT / "results") else [("pilot_output.txt", "differs", "")]


def main():
    new = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "outputs"
    problems, worst, exact, same_bytes = compare_grid(new / "grid_results.csv")
    print(f"grid_results.csv: {problems:,} problems; largest difference {worst:.3g}; "
          f"design and flags equal: {exact}; same bytes: {same_bytes}")
    search_failures, rows_differ, largest = compare_searches(new)
    print(f"searches: largest gap / bound {largest:.3f} (paper: at most 0.5); "
          f"rows that differ from the saved files, which is allowed: {rows_differ}")
    found = compare_summary(new) + search_failures + compare_pilot(new)
    for path, a, b in found:
        print(f"  {path}: new={a} saved={b}")
    print(f"summary.json, Table 3, Figure 1 data, searches and pilot: {len(found)} differences")
    return 0 if exact and worst <= TOL and not found else 1


if __name__ == "__main__":
    sys.exit(main())
