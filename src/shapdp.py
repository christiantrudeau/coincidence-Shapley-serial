"""Exact Shapley value of the optimistic cost function for scheduling problems with
discretely divisible jobs, C(S) = w0 * sum_{t in S} ceil(l_{S<=t} / k), computed by a
dynamic program over (coalition size, sum of lengths mod k).  Complexity O(n^3 k).

Marginal contribution of i to S (agents sorted by length, i not in S):
  ceil((L_{<i}(S) + l_i)/k)  +  sum_{t in S, t > i} [ceil((L_t(S) + l_i)/k) - ceil(L_t(S)/k)]
The bracket depends only on r = L_t(S) mod k:  delta(r, a) = ceil((r+a)/k) - [r > 0].
The first term is split as ceil(y/k) = (y + ((-y) mod k)) / k.
"""
import numpy as np
from math import comb, factorial, lgamma, exp
from operator import index


def checked_lengths(l):
    """Lengths are positive integers (l_i in N). index() accepts Python and numpy integers and
    refuses anything else; the conversion to Python ints avoids int64 overflow in comb(...) * Lam."""
    l = [index(x) for x in l]
    if min(l) < 1:
        raise ValueError("job lengths must be positive integers")
    return l


def pi_weights(n):
    # pi(s) = s!(n-s-1)!/n! = 1 / (n * C(n-1, s)),  s = 0..n-1
    return np.array([1.0 / (n * comb(n - 1, s)) for s in range(n)])


def shapley_opt_div(l, k, w0=1.0):
    l = checked_lengths(l)
    n = len(l)
    order = sorted(range(n), key=lambda i: (l[i], i))
    ls = [l[i] for i in order]
    pi = pi_weights(n)
    # V[m][a] = sum_b C(m, b) pi(a + b)  (m agents available after, a before)
    V = np.zeros((n + 1, n))
    for m in range(n + 1):
        for a in range(n):
            s = 0.0
            for b in range(0, m + 1):
                if a + b <= n - 1:
                    s += comb(m, b) * pi[a + b]
            V[m, a] = s
    # W[m][a] = sum_b C(m, b) pi(a + 1 + b)
    W = np.zeros((n + 1, n))
    for m in range(n + 1):
        for a in range(n - 1):
            s = 0.0
            for b in range(0, m + 1):
                if a + 1 + b <= n - 1:
                    s += comb(m, b) * pi[a + 1 + b]
            W[m, a] = s
    sh = np.zeros(n)
    rvec = np.arange(k)
    for ii in range(n):  # position in sorted order
        li = ls[ii]
        # residue DP over agents before ii (positions 0..ii-1)
        D = np.zeros((n, k))
        D[0, 0] = 1.0
        Lam = 0
        for t in range(ii):
            D = add_agent(D, ls[t], k)
            Lam += ls[t]
        # own term: sum_a V[n-1-ii][a] * [ (C(ii-1, a-1) Lam + C(ii, a) li)/k + sum_r D[a,r] ((-r-li) mod k)/k ]
        m_after = n - 1 - ii
        own = 0.0
        modterm = ((-rvec - li) % k) / k
        for a in range(ii + 1):
            lin = ((comb(ii - 1, a - 1) * Lam if a >= 1 and ii >= 1 else 0.0) + comb(ii, a) * li) / k
            own += V[m_after, a] * (lin + D[a] @ modterm)
        # followers term
        delta = np.array([-(-(r + li) // k) - (1 if r > 0 else 0) for r in range(k)], dtype=float)
        foll = 0.0
        for t in range(ii + 1, n):
            lt = ls[t]
            # residue of L_t(S) = (r + lt) mod k
            rot = delta[(rvec + lt) % k]
            m_after_t = n - 1 - t
            foll += W[m_after_t, :] @ (D @ rot)
            D = add_agent(D, lt, k)
        sh[order[ii]] = own + foll
    return w0 * sh


def add_agent(D, length, k):
    shifted = np.roll(D, length % k, axis=1)
    newD = D.copy()
    newD[1:] += shifted[:-1]
    return newD


def grand_cost(l, k, w0=1.0):
    pre = 0
    c = 0
    for x in sorted(l):
        pre += x
        c += -(-pre // k)
    return w0 * c


def serial_div(l, k, w0=1.0):
    l = checked_lengths(l)
    n = len(l)
    order = sorted(range(n), key=lambda i: (l[i], i))
    ls = [l[i] for i in order]
    y = np.zeros(n)
    prev = 0.0
    acc = 0.0
    for q in range(n):
        cap = ls[q]
        c = grand_cost([min(x, cap) for x in ls], k, w0)
        acc += (c - prev) / (n - q)
        y[order[q]] = acc
        prev = c
    return y


def completion_times(l, k):
    n = len(l)
    order = sorted(range(n), key=lambda i: (l[i], i))
    C = np.zeros(n)
    pre = 0
    for i in order:
        pre += l[i]
        C[i] = -(-pre // k)
    return C


# ---------------------------------------------------------------- brute force check
def brute_shapley(l, k):
    n = len(l)
    order = sorted(range(n), key=lambda i: (l[i], i))
    v = np.zeros(1 << n)
    for mask in range(1, 1 << n):
        pre = 0
        c = 0
        for i in order:
            if mask >> i & 1:
                pre += l[i]
                c += -(-pre // k)
        v[mask] = c
    w = [factorial(s) * factorial(n - s - 1) / factorial(n) for s in range(n)]
    pc = [bin(m).count("1") for m in range(1 << n)]
    sh = np.zeros(n)
    for m in range(1 << n):
        for i in range(n):
            if not m >> i & 1:
                sh[i] += w[pc[m]] * (v[m | 1 << i] - v[m])
    return sh


if __name__ == "__main__":
    import random
    random.seed(0)
    worst = 0.0
    for trial in range(400):
        n = random.randint(1, 11)
        k = random.choice([1, 2, 3, 4, 5, 8, 16])
        l = [random.randint(1, 3 * k + 2) for _ in range(n)]
        a = shapley_opt_div(l, k)
        b = brute_shapley(l, k)
        worst = max(worst, float(np.max(np.abs(a - b))))
    print("max |DP - brute force| over 400 random problems (n<=11):", worst)
    print("running example l=(2,3,6), k=2:", shapley_opt_div([2, 3, 6], 2), serial_div([2, 3, 6], 2))
    # k=1 and multiples of k: Shapley must equal serial
    bad = 0
    for trial in range(200):
        n = random.randint(2, 30); k = random.choice([2, 3, 4, 8])
        l = [k * random.randint(1, 6) for _ in range(n)]
        bad += np.max(np.abs(shapley_opt_div(l, k) - serial_div(l, k))) > 1e-8
    print("multiples of k, n up to 30: mismatches", bad)
