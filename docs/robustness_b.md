# Robustness check: small changes in length

The main study draws lengths at random, so most of them are not multiples of $k$. This check asks how
little it takes to separate the two rules. It starts from problems where every length is a multiple of
$k$, where the optimistic Shapley value and the serial rule coincide (Remark 3 of the paper), and changes a
few lengths by one unit.

| | |
| --- | --- |
| Code | [`src/robustness_b.py`](../src/robustness_b.py), [`src/summarize_b.py`](../src/summarize_b.py) |
| Data | [`data/robustness_b.csv.gz`](../data/robustness_b.csv.gz): 213,840 problems, one per row |
| Results | [`results/robustness_b_summary.json`](../results/robustness_b_summary.json), all tables in [`results/robustness_b_tables.md`](../results/robustness_b_tables.md) |
| Tests | [`tests/test_robustness_b.py`](../tests/test_robustness_b.py) |

## Design

The check uses the values of the main study: $n \in \lbrace 5, 10, 20, 50, 100 \rbrace$,
$k \in \lbrace 2, 4, 8, 16 \rbrace$, $\rho \in \lbrace 0.5, 1, 2, 5, 10, 20 \rbrace$ and the three length
distributions of [`how_the_data_is_generated.md`](how_the_data_is_generated.md), with 50, 50, 50, 20 and
10 repetitions by $n$. That gives 12,960 base problems.

1. **Base problem.** Lengths are drawn as in the main study and rounded to multiples of $k$:
   $l_i = k \max(1, \mathrm{rint}(\rho x_i))$. The rules coincide in every base problem.
2. **Changes.** A random order of the agents is drawn once. The first $m$ agents in that order have their
   length changed by one unit, for $m \in \lbrace 1, 2, 3, 5, 10, n/4, n/2, n \rbrace$: all up, all down, or
   alternately up and down ("mixed", for $m \ge 2$).
3. **Paired comparison.** The changed sets are nested ($m = 1$ is inside $m = 2$, and so on), and every $m$
   and direction is applied to the same base problem. Each problem has its own seed, from
   `crc32("B-n-k-rho-dist-rep")`.

The measures are those of the main study, plus the gap of the changed agents and of the others. Column
meanings are in the `one` function of `src/robustness_b.py`.

## Results

**One length changed by one unit**: share of problems where the rules differ, and the largest gap as a %
of the average share, median (95th percentile).

| | $n=5$ | $n=10$ | $n=20$ | $n=50$ | $n=100$ |
| --- | --- | --- | --- | --- | --- |
| Rules differ, up / down (%) | 61 / 37 | 76 / 57 | 86 / 79 | 89 / 91 | 90 / 95 |
| Gap, length up | 3.1 (20.9) | 6.7 (24.0) | 7.0 (25.0) | 7.6 (25.3) | 7.7 (25.0) |
| Gap, length down | 0.0 (37.5) | 1.4 (43.1) | 2.4 (45.2) | 4.2 (46.6) | 4.7 (47.0) |

**$n = 100$**: median largest gap (% of the average share) by the number $m$ of lengths changed.

| $m$ | 1 | 2 | 3 | 5 | 10 | 25 | 50 | 100 (all) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Up | 7.7 | 4.2 | 2.7 | 1.5 | 0.7 | 0.4 | 0.3 | 0 |
| Down | 4.7 | 5.0 | 5.1 | 3.7 | 2.5 | 0.8 | 0.4 | 0 |
| Mixed | | 5.5 | 7.8 | 6.0 | 3.7 | 1.9 | 0.8 | 0.2 |

- **One unit is enough.** With one length changed, the rules differ in 49% of the problems with $n = 5$
  and 93% with $n = 100$. The gap does not shrink as $n$ grows. At $n = 100$ its median is 4.7 to 7.7% of
  the average share, against 0.1 to 1.9% in Table 3 of the paper, where most lengths are not multiples of $k$.
- **The changed agent carries most of the gap.** Its median gap is 4 to 6% of the average share, against
  0.1 to 0.7% for the others. On average the Shapley value charges it more than the serial rule, by 6 to 10%
  of the average share, whether its job became longer or shorter. Many agents get a small gap all the
  same: 43 of 100 at the median.
- **More changes in the same direction shrink the gap**, to zero when every length changes. Mixed changes
  keep it. The next section explains why.
- **Longer jobs reduce the gap.** With one change and $n \ge 10$, its median is 1.4 to 1.9% at
  $\rho = 20$, against 8.6 to 12.1% at $\rho = 1$. When the changed job is the longest and becomes longer, the rules
  always coincide.
- **The bound.** The largest gap is exactly half of the bound of Proposition 2. It occurs for $n = 10$,
  $k = 2$ and one job shortened from 2 to 1, which is the paper's tightness example
  $l = (1, k, \ldots, k)$. No gap exceeds half of the bound, as in Section 6.

## Equal remainders: the rules coincide

**Claim.** If all lengths have the same remainder $r$ modulo $k$, then the optimistic Shapley value and the
serial rule coincide. Remark 3 of the paper is the case $r = 0$.

**Proof.** Take $t \in S$, and let $c$ be the number of members of $S$ up to and including $t$. Then
$l_{S_{\le t}} \equiv c\,r \pmod k$. Since $\lceil y/k \rceil = (y + ((-y) \bmod k))/k$,

```math
C_o^D(S) = \frac{w_0}{k} \sum_{t \in S} l_{S_{\le t}} \; + \; g(|S|),
\qquad g(s) = \frac{w_0}{k} \sum_{c=1}^{s} \bigl((-c\,r) \bmod k\bigr).
```

The first part is the single-server cost with lengths $l_i/k$, for which the two rules coincide (Moulin,
2007). The second part depends only on the size of the coalition, so the Shapley value splits $g(n)$
equally. The serial rule's intermediate profiles, with lengths $\min(l_i, l_q)$, keep the remainder $r$,
so $g(n)$ enters only its first step, where it is also split equally. Both rules are additive across the
two parts, so they coincide.

**Checks.** Every one of the 42,120 problems in this check whose lengths share one remainder coincides.
`tests/test_robustness_b.py` also checks the claim in exact rational arithmetic on random problems.

This explains the pattern above: the gap comes from lengths with **different** remainders, not from
lengths that are not multiples of $k$. Changing every length by one unit in the same direction gives them
all the same remainder again. Mixed changes do so only when $k = 2$, since $+1$ and $-1$ then give the same
remainder, which is why 75% of the "all, mixed" problems differ (the three values of $k$ above 2).

## Accuracy

- None of the 12,960 base problems has a gap.
- Shares add up to the total cost within $6 \times 10^{-11}$.
- In 400 problems recomputed in exact rational arithmetic, the "rules differ" flag always agreed with the
  floating-point code, and the gaps agreed within $6 \times 10^{-14}$. `tests/test_robustness_b.py`
  repeats this on a random sample. The smallest nonzero gap in the check is 0.005 periods, far above the
  $10^{-9}$ threshold.

## Running it

From a separate folder, as for the main study:

```
mkdir outputs
cd outputs
python ../src/robustness_b.py      # robustness_b.csv
python ../src/summarize_b.py       # robustness_b_summary.json and robustness_b_tables.md
```

The first step took 26 minutes with 14 processes on the reference machine of
[`machine_and_run_times.md`](machine_and_run_times.md). By default it uses all logical processors;
`--processes P` sets another number. It is not part of `src/reproduce_all.py`.
