# How the data is generated

The study uses no external dataset. Every problem is simulated, and the file
[`data/grid_results.csv`](../data/grid_results.csv) is the output of
[`src/run_grid.py`](../src/run_grid.py). Anyone can regenerate it from the code: each problem has
its own fixed seed, so nothing is stored that cannot be rebuilt.

## 1. What a problem is

A problem is a list of job lengths $l_1,\dots,l_n$, positive integers, to be processed on $k$
servers. Jobs are discretely divisible, and the waiting cost per period is $w_0 = 1$; both rules are
proportional to $w_0$, so this loses no generality. For each problem the code computes the Shapley
value of the optimistic cost function and the serial rule, both exactly, and measures their distance.

## 2. The design: 78,480 problems

| Parameter | Values | Meaning |
| --- | --- | --- |
| `n` | 5, 10, 20, 50, 100 | Number of agents |
| `k` | 2, 4, 8, 16 | Number of servers |
| `rho` | 0.5, 1, 2, 5, 10, 20 | Target mean job length, in periods of full capacity (mean length / k) |
| `dist` | uniform, heavy, bimodal | Shape of the distribution of lengths |
| `rep` | 300 for n up to 20; 150 for n = 50; 40 for n = 100 | Replications per cell |

Each combination has 4 × 6 × 3 = 72 cells for a given `n`, which gives
72 × (300 + 300 + 300 + 150 + 40) = 78,480 problems.

## 3. From parameters to job lengths

**Step 1, the seed.** The seed comes from the problem's own parameters:
`zlib.crc32("n-k-rho-dist-rep")`. It does not depend on run order, so one problem can be rebuilt
alone, and the result does not depend on how many processes are used.

**Step 2, a base draw.** Each agent gets a draw $x_i$ with mean 1:

| `dist` | Distribution of $x_i$ | Mean | What it represents |
| --- | --- | --- | --- |
| uniform | Uniform(0, 2) | 1 | Similar jobs |
| heavy | Lognormal(-0.5, 1) | 1 | Many short jobs and a few very long ones |
| bimodal | 0.8 Uniform(0, 0.5) + 0.2 Uniform(2, 6) | 1 | Two groups: short and long jobs |

**Step 3, the length.** The draw is scaled and rounded to a positive integer:

$$l_i = \max\{1, \operatorname{rint}(k \, \rho \, x_i)\}.$$

Rounding and the minimum of 1 can move the realized mean away from the target, so the file records
`mean_len_over_k`. Across the design it averages 0.57 for `rho` = 0.5, where the minimum length of 1
matters most, and stays within 0.08 of the target for the other values.

## 4. A worked example

Take `n = 5`, `k = 2`, `rho = 2`, `dist = uniform`, `rep = 0`.

| Step | Result |
| --- | --- |
| Text for the seed | `5-2-2-uniform-0` |
| Seed | 1510836008 |
| Draws $x_i$ | 1.894, 1.282, 1.366, 1.245, 0.344 |
| Lengths $l_i = \max\{1, \operatorname{rint}(4x_i)\}$ | 8, 5, 5, 5, 1 |
| Total cost $C(N)$ | 30 |
| Shapley value | 8.2, 6.7, 6.7, 6.7, 1.7 |
| Serial rule | 7.8, 6.8, 6.8, 6.8, 1.8 |
| Largest difference, relative to the average share of 6 (`gmax`) | 0.4 / 6 = 0.0667 |

To rebuild one problem yourself, from the `src` folder:

```python
from run_grid import one
print(one((5, 2, 2, "uniform", 0)))     # n, k, rho, dist, rep
```

## 5. Columns of `grid_results.csv`

For each problem, with $d_i = Sh_i(C_o^D) - Ser_i^D$ and average share $C^D(N)/n$:

| Column | Meaning |
| --- | --- |
| `n`, `k`, `rho_target`, `dist`, `rep` | Design parameters and replication number |
| `mean_len_over_k` | Realized mean job length divided by k |
| `min_len` | Shortest length |
| `frac_nonmult` | Share of lengths that are not multiples of k |
| `gmax`, `gmean` | Largest and mean $\lvert d_i\rvert$, relative to the average share |
| `g_agent` | Largest $\lvert d_i\rvert / Ser_i$ |
| `g_bound` | Largest $\lvert d_i\rvert$ divided by $2n(k-1)/k$; twice this is the gap as a fraction of the bound of Proposition 2 |
| `realloc` | $\frac{1}{2}\sum_i \lvert d_i\rvert / C^D(N)$, the share of total cost that changes hands |
| `g_transfer` | $\sum_i \lvert d_i\rvert / \sum_i \lvert Ser_i - C_i\rvert$, relative to the transfers of the serial rule |
| `any_diff` | Whether the two rules differ, that is, whether the largest $\lvert d_i\rvert$ is above $10^{-9}$ |
| `d_long`, `d_short` | $d_i$ for the longest and the shortest job, relative to the average share |

## 6. The two other sources of numbers

**Hill-climbing searches.** `src/adversarial_search.py` and `src/adversarial_search_n16.py` do not
sample at random across the design. They start from random integer lengths and repeatedly change one
or two jobs, keeping any change that does not lower the objective, to look for the largest gaps. The
first covers n from 3 to 8; the second covers n = 10, 12 and 16. Both use k in {2, 3, 4, 8} and
lengths up to 4k, with fixed seeds (7 and 11).

**Pilot study.** `src/pilot_pessimistic.py` draws 1,800 small problems (n in {6, 8, 10}, k in
{2, 3, 4}), with lengths uniform on 1 to 5 or 1 to 20 and seed 2026. It uses brute force, which also
allows the pessimistic cost functions.
