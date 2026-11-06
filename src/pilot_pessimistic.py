"""Pilot numerical study: size of Shapley vs serial gaps in multi-server scheduling (w0 = 1)."""
import random, statistics as st
from math import factorial
import numpy as np

def costs_all(ls, k, kind):
    """cost of every coalition (bitmask) for scheduling problems, agents sorted by length"""
    n = len(ls); L = sum(ls); out = np.zeros(1 << n)
    for mask in range(1, 1 << n):
        members = [i for i in range(n) if mask >> i & 1]
        if kind in ("oD", "pD"):
            pre = 0 if kind == "oD" else L - sum(ls[i] for i in members)
            c = 0
            for i in members:
                pre += ls[i]; c += -(-pre // k)
        else:
            loads = [0] * k
            if kind == "pI":
                for i in range(n):
                    if not mask >> i & 1:
                        m = loads.index(min(loads)); loads[m] += ls[i]
            c = 0
            for i in members:
                m = loads.index(min(loads)); loads[m] += ls[i]; c += loads[m]
        out[mask] = c
    return out

def shapley(v, n):
    wts = [factorial(s) * factorial(n - s - 1) / factorial(n) for s in range(n)]
    sh = np.zeros(n)
    pc = [bin(m).count("1") for m in range(1 << n)]
    for mask in range(1 << n):
        s = pc[mask]
        for i in range(n):
            if not mask >> i & 1:
                sh[i] += wts[s] * (v[mask | 1 << i] - v[mask])
    return sh

def grand(ls, k, R):
    return costs_all(ls, k, "o" + R)[(1 << len(ls)) - 1] if len(ls) <= 12 else None

def grand_fast(ls, k, R):
    ls = sorted(ls)
    if R == "D":
        pre = c = 0
        for x in ls:
            pre += x; c += -(-pre // k)
        return c
    loads = [0] * k; c = 0
    for x in ls:
        m = loads.index(min(loads)); loads[m] += x; c += loads[m]
    return c

def serial(ls, k, R, dec=False):
    n = len(ls); idx = sorted(range(n), key=lambda i: ls[i], reverse=dec)
    y = np.zeros(n); prev = None
    for q in range(n):
        cap = ls[idx[q]]
        prof = [max(t, cap) if dec else min(t, cap) for t in ls]
        c = grand_fast(prof, k, R); inc = c if prev is None else c - prev
        for r in range(q, n):
            y[idx[r]] += inc / (n - q)
        prev = c
    return y

def pattern(y, ls, tol=1e-9):
    pres = all(y[i] <= y[j] + tol for i in range(len(ls)) for j in range(len(ls)) if ls[i] < ls[j])
    rev = all(y[i] >= y[j] - tol for i in range(len(ls)) for j in range(len(ls)) if ls[i] < ls[j])
    return "both" if pres and rev else "pres" if pres else "rev" if rev else "neither"

random.seed(2026)
print("n k lmax | oD: %differ  mean/max gap (%avg share) | pD vs DSer: mean/max gap | pD pattern | pI pattern (pres/rev/neither)")
rows = []
for n in (6, 8, 10):
    for k in (2, 3, 4):
        for lmax in (5, 20):
            T = 120 if n < 10 else 60
            g_o, g_p, differ = [], [], 0
            patD, patI = {}, {}
            mult_ok = True
            for _ in range(T):
                ls = sorted(random.randint(1, lmax) for _ in range(n))
                CN = grand_fast(ls, k, "D"); avg = CN / n
                sho = shapley(costs_all(ls, k, "oD"), n); ser = serial(ls, k, "D")
                shp = shapley(costs_all(ls, k, "pD"), n); dser = serial(ls, k, "D", True)
                shpI = shapley(costs_all(ls, k, "pI"), n)
                go = np.max(np.abs(sho - ser)) / avg; gp = np.max(np.abs(shp - dser)) / avg
                g_o.append(go); g_p.append(gp); differ += go > 1e-9
                patD[pattern(shp, ls)] = patD.get(pattern(shp, ls), 0) + 1
                patI[pattern(shpI, ls)] = patI.get(pattern(shpI, ls), 0) + 1
            rows.append((n, k, lmax, differ / T, st.mean(g_o), max(g_o), st.mean(g_p), max(g_p), patD, patI))
            print(f"{n:2d} {k} {lmax:3d} | {100*differ/T:5.1f}%  {100*st.mean(g_o):5.1f}/{100*max(g_o):5.1f} | {100*st.mean(g_p):6.1f}/{100*max(g_p):6.1f} | {patD} | {patI}")

# lengths that are multiples of k: coincidence should be exact (divisible = single fast server)
random.seed(5); bad = 0
for _ in range(100):
    n = random.randint(3, 8); k = random.randint(2, 4)
    ls = sorted(k * random.randint(1, 6) for _ in range(n))
    bad += np.max(np.abs(shapley(costs_all(ls, k, "oD"), n) - serial(ls, k, "D"))) > 1e-9
print("multiples of k: Sh(Co^D) != Ser^D in", bad, "of 100")

# runtime illustration: exact Shapley vs serial
import time
for n in (10, 14, 16):
    ls = sorted(random.randint(1, 20) for _ in range(n))
    t = time.time(); serial(ls, 3, "D"); ts = time.time() - t
    t = time.time(); shapley(costs_all(ls, 3, "oD"), n); th = time.time() - t
    print(f"n={n}: serial {ts*1000:.2f} ms, exact Shapley {th:.1f} s")
