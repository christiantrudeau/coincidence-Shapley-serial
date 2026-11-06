"""Recomputes, from the definitions and with exact fractions, every number quoted in
Sections 2-5 of the paper, plus random-problem checks of Lemma 1, Theorem 1, Proposition 1
and Theorem 2.
Run: python tests/ejor_rr_checks.py   (standard library only; about a minute)"""
import random
from fractions import Fraction as F
from itertools import product
from math import factorial

RESULTS = []


def check(label, got, expected):
    ok = got == expected
    RESULTS.append(ok)
    print(f"[{'PASS' if ok else 'FAIL'}] {label}: {fmt(got)}" + ("" if ok else f"   expected {fmt(expected)}"))


def fmt(x):
    if isinstance(x, (list, tuple)):
        return "(" + ", ".join(fmt(v) for v in x) + ")"
    return str(x)


def ceil_div(a, b):
    return -(-a // b)


# ------------------------------------------------------------------ greedy schedules
def greedy(jobs, k, avail=None, divisible=False):
    """Algorithm 1. jobs = list of (agent, length) in order of urgency. Returns
    (completion times by agent, final availability times)."""
    a = list(avail) if avail else [0] * k
    done = {}
    for agent, length in jobs:
        tasks = [1] * length if divisible else [length]
        finish = 0
        for t in tasks:
            m = min(range(k), key=lambda j: (a[j], j))   # first free server, lowest index on ties
            a[m] += t
            finish = max(finish, a[m])
        done[agent] = finish
    return done, a


# ------------------------------------------------------------------ cost functions (scheduling, w0 = 1)
def sched_order(S, l):
    return sorted(S, key=lambda i: (l[i], i))          # shortest job first


def cost_sched(S, l, k, R, kind):
    """C_o^R or C_p^R of coalition S (Definition 2), by the greedy algorithm."""
    S = list(S)
    if not S:
        return 0
    avail = None
    if kind == "p":
        rest = [i for i in range(len(l)) if i not in S]
        _, avail = greedy([(i, l[i]) for i in sched_order(rest, l)], k, divisible=(R == "D"))
    done, _ = greedy([(i, l[i]) for i in sched_order(S, l)], k, avail, divisible=(R == "D"))
    return sum(done.values())


def cost_queue(S, w, l0, k, R, kind):
    """Queueing closed forms of Table 1 (agents served by decreasing w)."""
    S = sorted(S, key=lambda i: (-w[i], i))
    n, s = len(w), len(S)
    c = 0
    for r, i in enumerate(S, start=1):
        rank = r if kind == "o" else n - s + r
        c += (l0 * ceil_div(rank, k) if R == "I" else ceil_div(rank * l0, k)) * w[i]
    return c


# ------------------------------------------------------------------ Shapley value and serial rules
def shapley(n, C):
    v = {}
    for mask in range(1 << n):
        v[mask] = C([i for i in range(n) if mask >> i & 1])
    sh = [F(0)] * n
    for mask in range(1 << n):
        s = bin(mask).count("1")
        for i in range(n):
            if not mask >> i & 1:
                sh[i] += F(factorial(s) * factorial(n - s - 1), factorial(n)) * (v[mask | 1 << i] - v[mask])
    return sh


def serial(theta, total):
    """Definition 3, serial rule. total(theta') = C^R(N, theta')."""
    n = len(theta)
    inc = sorted(range(n), key=lambda i: (theta[i], i))
    pos = {i: q for q, i in enumerate(inc, start=1)}
    vals = [theta[i] for i in inc]
    costs = [0] + [total([min(t, vals[q - 1]) for t in theta]) for q in range(1, n + 1)]
    return [sum(F(costs[q] - costs[q - 1], n - q + 1) for q in range(1, pos[i] + 1)) for i in range(n)]


def dserial(theta, total):
    """Definition 3, decreasing serial rule."""
    n = len(theta)
    dec = sorted(range(n), key=lambda i: (-theta[i], i))
    pos = {i: q for q, i in enumerate(dec, start=1)}
    vals = [theta[i] for i in dec]
    costs = [0] + [total([max(t, vals[q - 1]) for t in theta]) for q in range(1, n + 1)]
    return [sum(F(costs[q] - costs[q - 1], n - q + 1) for q in range(1, pos[i] + 1)) for i in range(n)]


def total_sched(k, R):
    return lambda l: cost_sched(range(len(l)), l, k, R, "o")


def rules_sched(l, k):
    n = len(l)
    out = {}
    for R in "ID":
        out["Sh_o" + R] = shapley(n, lambda S: cost_sched(S, l, k, R, "o"))
        out["Sh_p" + R] = shapley(n, lambda S: cost_sched(S, l, k, R, "p"))
        out["Ser" + R] = serial(l, total_sched(k, R))
        out["DSer" + R] = dserial(l, total_sched(k, R))
    return out


# ------------------------------------------------------------------ brute-force optimal schedules
def opt_indivisible(w, l, k, avail=None):
    """Exact optimum: every assignment of jobs to servers, Smith's order on each server."""
    n, a0 = len(l), avail or [0] * k
    best = None
    for assign in product(range(k), repeat=n):
        cost = 0
        for m in range(k):
            t = a0[m]
            for i in sorted([i for i in range(n) if assign[i] == m], key=lambda i: -F(w[i], l[i])):
                t += l[i]
                cost += w[i] * t
        best = cost if best is None else min(best, cost)
    return best


def opt_divisible(w, l, k, avail=None):
    """Exact optimum by search over period-by-period allocations of unit tasks."""
    a0 = avail or [0] * k
    n = len(l)
    memo = {}

    def go(t, rem):                        # t = periods elapsed, rem = units left per agent
        if not any(rem):
            return 0
        key = (t, rem)
        if key in memo:
            return memo[key]
        cap = sum(1 for am in a0 if am <= t)          # servers available in period t+1
        if cap == 0:
            memo[key] = go(t + 1, rem)
            return memo[key]
        best = None
        live = [i for i in range(n) if rem[i]]
        for x in product(*[range(min(rem[i], cap) + 1) for i in live]):
            if not 1 <= sum(x) <= cap:                   # idling never lowers any completion time
                continue
            new = list(rem)
            c = 0
            for i, xi in zip(live, x):
                new[i] -= xi
                if new[i] == 0:
                    c += w[i] * (t + 1)
            sub = go(t + 1, tuple(new))
            best = c + sub if best is None else min(best, c + sub)
        memo[key] = best
        return best

    return go(0, tuple(l))


def greedy_cost(w, l, k, order, R, avail=None):
    done, _ = greedy([(i, l[i]) for i in order], k, avail, divisible=(R == "D"))
    return sum(w[i] * done[i] for i in order)


# ================================================================== the checks
def section_2():
    print("\n== Section 2: Example 1 (l = (2,3,6), k = 2, w0 = 1) and remarks")
    l, k = [2, 3, 6], 2
    dD, _ = greedy([(i, l[i]) for i in range(3)], k, divisible=True)
    dI, _ = greedy([(i, l[i]) for i in range(3)], k)
    check("divisible completion times", [dD[i] for i in range(3)], [1, 3, 6])
    check("C^D(N)", sum(dD.values()), 10)
    check("indivisible completion times", [dI[i] for i in range(3)], [2, 3, 8])
    check("C^I(N)", sum(dI.values()), 13)
    check("greedy optimal, divisible (brute force)", opt_divisible([1] * 3, l, k), 10)
    check("greedy optimal, indivisible (brute force)", opt_indivisible([1] * 3, l, k), 13)
    ser = serial(l, total_sched(k, "D"))
    check("transfers t = Ser^D - completion", [ser[i] - dD[i] for i in range(3)], [1, 0, -1])
    check("C_p^D({1,2})", cost_sched([0, 1], l, k, "D", "p"), 10)
    table = {(0,): (2, 5, 1, 6), (1,): (3, 5, 2, 6), (2,): (6, 8, 3, 6), (0, 1): (5, 7, 4, 10),
             (0, 2): (8, 10, 5, 9), (1, 2): (9, 11, 7, 9), (0, 1, 2): (13, 13, 10, 10)}
    for S, exp in table.items():
        got = tuple(cost_sched(S, l, k, R, kind) for R, kind in [("I", "o"), ("I", "p"), ("D", "o"), ("D", "p")])
        check(f"coalition table, S = {{{','.join(str(i + 1) for i in S)}}} (C_o^I, C_p^I, C_o^D, C_p^D)", got, exp)
    check("underline-theta^2", [min(t, 3) for t in l], [2, 3, 3])
    check("overline-theta^2", [max(t, 3) for t in l], [3, 3, 6])

    print("-- Remark 1 (problems that are not agreeable)")
    w, l1 = [3, 2, 3], [1, 1, 2]
    check("indivisible k=2, order 1,2,3 first free server", greedy_cost(w, l1, 2, [0, 1, 2], "I"), 14)
    check("indivisible optimum (brute force)", opt_indivisible(w, l1, 2), 13)
    w, l2 = [4, 6, 3], [1, 2, 3]
    check("divisible k=2, order 1,2,3", greedy_cost(w, l2, 2, [0, 1, 2], "D"), 25)
    check("divisible, agent 2 first", greedy_cost(w, l2, 2, [1, 0, 2], "D"), 23)
    check("divisible optimum (brute force)", opt_divisible(w, l2, 2), 23)

    print("-- Remark 2 (the complement's schedule)")
    l3 = [1, 3, 4, 5, 5]
    rest = [0, 1, 2, 4]
    _, av = greedy([(i, l3[i]) for i in rest], 2)
    check("greedy availability of N\\{4}", sorted(av), [5, 8])
    check("C_p^I(S={4}) with the greedy convention", cost_sched([3], l3, 2, "I", "p"), 10)
    check("cost of S={4} after availability (6,7)", 6 + 5, 11)
    check("both complement schedules optimal (cost 17)",
          (greedy_cost([1] * 5, l3, 2, rest, "I"), opt_indivisible([1, 1, 1, 1], [1, 3, 4, 5], 2)), (17, 17))


def section_3():
    print("\n== Section 3: serial walk-through, Table 2, Proposition 1, Remark 3, Proposition 2")
    l, k = [2, 3, 6], 2
    tot = total_sched(k, "D")
    check("serial path costs C^D(underline-theta^q)", [tot([min(t, v) for t in l]) for v in (2, 3, 6)], [6, 8, 10])
    check("decreasing serial path costs C^D(overline-theta^q)", [tot([max(t, v) for t in l]) for v in (6, 3, 2)], [18, 11, 10])
    r = rules_sched(l, k)
    table2 = {"Sh_oI": [F(8, 3), F(11, 3), F(20, 3)], "SerI": [F(8, 3), F(11, 3), F(20, 3)],
              "Sh_pI": [3, F(7, 2), F(13, 2)], "DSerI": [F(3, 2), F(7, 2), 8],
              "Sh_oD": [2, F(7, 2), F(9, 2)], "SerD": [2, 3, 5],
              "Sh_pD": [F(7, 2), F(7, 2), 3], "DSerD": [F(3, 2), F(5, 2), 6]}
    for key, exp in table2.items():
        check(f"Table 2, {key}", r[key], [F(x) for x in exp])

    l1 = [2, 4, 6]
    check("k=1, l=(2,4,6): Sh(C_p) (Chun 2007 counterexample)", shapley(3, lambda S: cost_sched(S, l1, 1, "I", "p")), [7, 7, 6])
    check("k=1, l=(2,4,6): DSer", dserial(l1, total_sched(1, "I")), [1, 7, 12])

    print("-- Remark 3 (why the coincidence fails)")
    def co(S, ll): return cost_sched(S, ll, 2, "D", "o")
    a, b = [2, 3, 3], [2, 3, 6]
    check("packing: raise l3 3->6, change in C_o^D of {3},{1,3},{2,3}",
          [co(S, b) - co(S, a) for S in ([2], [0, 2], [1, 2])], [1, 1, 2])
    def cp(S, ll): return cost_sched(S, ll, 2, "D", "p")
    check("spillover: lower l1,l2 6->3, change in C_p^D({3})", cp([2], [3, 3, 6]) - cp([2], [6, 6, 6]), -3)

    print("-- Proposition 2 tight example l = (1,k,...,k), n multiple of k")
    for k2, n2 in [(2, 4), (2, 6), (3, 6), (4, 8)]:
        l2 = [1] + [k2] * (n2 - 1)
        sh = shapley(n2, lambda S: cost_sched(S, l2, k2, "D", "o"))
        se = serial(l2, total_sched(k2, "D"))
        check(f"k={k2}, n={n2}: (Sh_1, Ser_1, Sh_1-Ser_1)", (sh[0], se[0], sh[0] - se[0]),
              (F(n2 + 1, 2), F(n2 + k2, 2 * k2), F(n2 * (k2 - 1), 2 * k2)))


def section_3_order():
    print("\n== Theorem 2(iii) and Section 5")
    l = [1, 2, 3, 4]
    check("k=2, l=(1,2,3,4): Sh(C_p^I)", shapley(4, lambda S: cost_sched(S, l, 2, "I", "p")),
          [F(31, 12), F(13, 4), F(37, 12), F(49, 12)])
    def sho(ll): return shapley(len(ll), lambda S: cost_sched(S, ll, 2, "D", "o"))
    sd = total_sched(2, "D")
    check("Sh(C_o^D) for l=(2,3,3)", sho([2, 3, 3]), [2, 3, 3])
    check("Sh(C_o^D) for l=(2,3,6)", sho([2, 3, 6]), [2, F(7, 2), F(9, 2)])
    check("Ser^D on P_-3, l=(2,3)", serial([2, 3], sd), [F(3, 2), F(5, 2)])
    check("Ser^D on P_-2, l=(2,6)", serial([2, 6], sd), [F(3, 2), F(7, 2)])
    full = serial([2, 3, 6], sd)
    check("serial: removing 3 lowers 2's share by", full[1] - F(5, 2), F(1, 2))
    check("serial: removing 2 lowers 3's share by", full[2] - F(7, 2), F(3, 2))


def random_checks(rng):
    print("\n== Random problems (brute force, exact fractions)")
    # Lemma 1: greedy optimal for agreeable problems, from arbitrary availability times
    bad = 0
    for _ in range(150):
        n, k = rng.randint(1, 4), rng.randint(1, 3)
        l = sorted(rng.randint(1, 4) for _ in range(n))
        w = sorted((rng.randint(1, 5) for _ in range(n)), reverse=True)   # agreeable
        av = [rng.randint(0, 3) for _ in range(k)]
        for R, opt in (("I", opt_indivisible), ("D", opt_divisible)):
            bad += greedy_cost(w, l, k, list(range(n)), R, av) != opt(w, l, k, av)
    check("Lemma 1: greedy optimal, 150 agreeable problems x {I,D}, random availability: mismatches", bad, 0)

    # Theorem 1 coincidences and Theorem 2(i)-(ii) order properties
    bad_q = bad_s = bad_order = 0
    fail_cases = {"Sh_oD != SerD": 0, "Sh_pD != DSerD": 0, "Sh_pI != DSerI": 0}
    for _ in range(120):
        n, k, l0 = rng.randint(2, 5), rng.randint(1, 3), rng.randint(1, 3)
        w = [rng.randint(1, 6) for _ in range(n)]
        for R in "ID":
            tq = lambda ww, R=R: cost_queue(range(n), ww, l0, k, R, "o")
            bad_q += shapley(n, lambda S: cost_queue(S, w, l0, k, R, "o")) != serial(w, tq)
            bad_q += shapley(n, lambda S: cost_queue(S, w, l0, k, R, "p")) != dserial(w, tq)
        l = [rng.randint(1, 6) for _ in range(n)]
        r = rules_sched(l, k)
        bad_s += r["Sh_oI"] != r["SerI"]
        fail_cases["Sh_oD != SerD"] += r["Sh_oD"] != r["SerD"]
        fail_cases["Sh_pD != DSerD"] += r["Sh_pD"] != r["DSerD"]
        fail_cases["Sh_pI != DSerI"] += r["Sh_pI"] != r["DSerI"]
        for i in range(n):
            for j in range(n):
                if l[i] < l[j]:
                    for key in ("SerI", "SerD", "DSerI", "DSerD", "Sh_oI", "Sh_oD"):
                        bad_order += r[key][i] > r[key][j]          # order preservation
                    bad_order += r["Sh_pD"][i] < r["Sh_pD"][j]       # order reversal
    check("Theorem 1(i): queueing, Sh = Ser and Sh_p = DSer, 120 problems x {I,D}: mismatches", bad_q, 0)
    check("Theorem 1(ii): scheduling, Sh(C_o^I) = Ser^I, 120 problems: mismatches", bad_s, 0)
    check("Theorem 2(i)-(ii): order preservation / reversal, 120 problems: violations", bad_order, 0)
    print("   (Proposition 1: the three non-coincidences occur in", fail_cases, "of 120 random problems)")
    check("Proposition 1: each non-coincidence occurs in random problems", all(v > 0 for v in fail_cases.values()), True)


if __name__ == "__main__":
    section_2()
    section_3()
    section_3_order()
    random_checks(random.Random(2026))
    print(f"\n{sum(RESULTS)} of {len(RESULTS)} checks passed.")
