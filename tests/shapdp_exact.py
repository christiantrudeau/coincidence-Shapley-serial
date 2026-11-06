"""Exact-arithmetic twin of shapdp.py, for testing: the same dynamic program, with every
quantity a Python int or fractions.Fraction, so the result is the exact rational Shapley value."""
from fractions import Fraction
from math import comb, factorial


def shapley_opt_div_exact(l, k):
    l = [int(x) for x in l]
    n = len(l)
    order = sorted(range(n), key=lambda i: (l[i], i))
    ls = [l[i] for i in order]
    pi = [Fraction(1, n * comb(n - 1, s)) for s in range(n)]
    # V[m][a] = sum_b C(m,b) pi(a+b);  W[m][a] = sum_b C(m,b) pi(a+1+b)
    V = [[sum((comb(m, b) * pi[a + b] for b in range(m + 1) if a + b <= n - 1), Fraction(0))
          for a in range(n)] for m in range(n + 1)]
    W = [[sum((comb(m, b) * pi[a + 1 + b] for b in range(m + 1) if a + 1 + b <= n - 1), Fraction(0))
          if a < n - 1 else Fraction(0) for a in range(n)] for m in range(n + 1)]
    sh = [Fraction(0)] * n
    for ii in range(n):
        li = ls[ii]
        D = [[0] * k for _ in range(n)]
        D[0][0] = 1
        Lam = 0
        for t in range(ii):
            D = add_agent(D, ls[t], k)
            Lam += ls[t]
        m_after = n - 1 - ii
        modnum = [(-r - li) % k for r in range(k)]          # numerators of ((-r-li) mod k)/k
        own = Fraction(0)
        for a in range(ii + 1):
            lin = (comb(ii - 1, a - 1) * Lam if a >= 1 and ii >= 1 else 0) + comb(ii, a) * li
            dot = sum(D[a][r] * modnum[r] for r in range(k))
            own += V[m_after][a] * Fraction(lin + dot, k)
        delta = [-(-(r + li) // k) - (1 if r > 0 else 0) for r in range(k)]
        foll = Fraction(0)
        for t in range(ii + 1, n):
            lt = ls[t]
            rot = [delta[(r + lt) % k] for r in range(k)]
            Drot = [sum(D[a][r] * rot[r] for r in range(k)) for a in range(n)]
            foll += sum((W[n - 1 - t][a] * Drot[a] for a in range(n) if Drot[a]), Fraction(0))
            D = add_agent(D, lt, k)
        sh[order[ii]] = own + foll
    return sh


def add_agent(D, length, k):
    s = length % k
    newD = [row[:] for row in D]
    for a in range(1, len(D)):
        prev = D[a - 1]
        row = newD[a]
        for r in range(k):
            row[(r + s) % k] += prev[r]
    return newD


def grand_cost_exact(l, k):
    pre = c = 0
    for x in sorted(l):
        pre += x
        c += -(-pre // k)
    return c


def serial_div_exact(l, k):
    l = [int(x) for x in l]
    n = len(l)
    order = sorted(range(n), key=lambda i: (l[i], i))
    ls = [l[i] for i in order]
    y = [Fraction(0)] * n
    prev, acc = 0, Fraction(0)
    for q in range(n):
        c = grand_cost_exact([min(x, ls[q]) for x in ls], k)
        acc += Fraction(c - prev, n - q)
        y[order[q]] = acc
        prev = c
    return y


def brute_shapley_exact(l, k):
    n = len(l)
    order = sorted(range(n), key=lambda i: (l[i], i))
    v = [0] * (1 << n)
    for mask in range(1, 1 << n):
        pre = c = 0
        for i in order:
            if mask >> i & 1:
                pre += l[i]
                c += -(-pre // k)
        v[mask] = c
    sh = [Fraction(0)] * n
    for m in range(1 << n):
        s = bin(m).count("1")
        for i in range(n):
            if not m >> i & 1:
                sh[i] += Fraction(factorial(s) * factorial(n - s - 1), factorial(n)) * (v[m | 1 << i] - v[m])
    return sh
