"""Adversarial search for the largest Shapley-serial gaps (optimistic, divisible, scheduling).
Random-restart hill climbing over integer length profiles.  Objectives:
  gmax    = max_i |Sh_i - Ser_i| / (C(N)/n)        (relative to the average share)
  g_bound = max_i |Sh_i - Ser_i| / (2 n (k-1)/k)   (2n(k-1)/k is twice the bound of Proposition 2,
                                                    so g_bound = 0.25 means half of that bound)
  g_agent = max_i |Sh_i - Ser_i| / Ser_i            (relative to the agent's own share)"""
import numpy as np, random, json, sys
from shapdp import shapley_opt_div, serial_div, grand_cost

def measures(l, k):
    sh = shapley_opt_div(l, k); se = serial_div(l, k); d = np.abs(sh - se); n = len(l)
    return dict(gmax=float(d.max() / (grand_cost(l, k) / n)),
                g_bound=float(d.max() / (2 * n * (k - 1) / k)),
                g_agent=float(np.max(d / se)))

def climb(n, k, lmax, obj, rng, iters=400):
    l = [rng.randint(1, lmax) for _ in range(n)]
    best = measures(l, k)[obj]
    for _ in range(iters):
        m = l[:]
        for _ in range(rng.choice([1, 1, 2])):
            i = rng.randrange(n)
            m[i] = max(1, min(lmax, m[i] + rng.choice([-2, -1, 1, 2]) if rng.random() < .7 else rng.randint(1, lmax)))
        v = measures(m, k)[obj]
        if v >= best:
            l, best = m, v
    return best, sorted(l)

if __name__ == "__main__":
    rng = random.Random(7)
    out = []
    for obj in ["gmax", "g_bound", "g_agent"]:
        for k in [2, 3, 4, 8]:
            for n in [3, 4, 5, 6, 8]:
                lmax = 4 * k
                res = max((climb(n, k, lmax, obj, rng) for _ in range(6)), key=lambda t: t[0])
                full = measures(res[1], k)
                out.append(dict(obj=obj, k=k, n=n, value=res[0], l=res[1], **{f"m_{a}": b for a, b in full.items()}))
                print(obj, k, n, round(res[0], 4), res[1], flush=True)
    json.dump(out, open("adv_results.json", "w"), indent=1)
