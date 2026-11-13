# Machine and run times

Reference machine: Huawei laptop, Intel Core Ultra 7 155H (16 cores, 22 threads), 31.5 GB RAM,
Windows 11, Python 3.14.7, numpy 2.5.3.

`src/run_grid.py` as written (2 processes): 1,097 s, about 18 minutes. The laptop was on battery for
the first minutes and plugged in afterwards; a run entirely on battery took 1,880 s, so the figure is
a guide rather than a precise benchmark.

`src/robustness_b.py` (robustness check, 12,960 base problems and 213,840 variants), 14 processes,
plugged in: 1,578 s, about 26 minutes.

Mean time per problem, one process, plugged in (rho = 2, uniform lengths, 20 problems; measured by
`src/benchmark.py`, saved in `results/benchmark.json`):

| n | 5 | 10 | 20 | 50 | 100 |
| --- | --- | --- | --- | --- | --- |
| Shapley (dynamic program), k = 2 | 0.31 ms | 1.3 ms | 5.9 ms | 50 ms | 0.34 s |
| Shapley (dynamic program), k = 16 | 0.34 ms | 1.3 ms | 6.3 ms | 55 ms | 0.35 s |
| Serial, k = 16 | 0.01 ms | 0.03 ms | 0.08 ms | 0.39 ms | 1.5 ms |

## Differences between computers

Unrounded values can differ in the last digits between computers, because processors and math
libraries round differently. This does not affect the theory or any reported number. The full study
was run on three systems: Windows 11 and Ubuntu 24.04 on the machine above, and macOS 26.6 on a
MacBook Air (Apple M1, 8 GB RAM), where `src/run_grid.py` took 612 s. `data/grid_results.csv` is
byte-identical on the first two and agrees to 3e-15 on the Apple chip, whose numpy uses another math
library.

The hill-climbing searches are the one place where this can be seen. Many of their moves tie exactly,
the last digits can decide whether a tie is accepted, and one decision sends the search down a
different route. On the Apple chip, the row k = 8, n = 12 of `results/adv2_results.json` ended at a
gap of 0.492 of the bound instead of 0.373. Both are correctly computed problems, and neither result
is more right than the other; the search looks for large gaps and has no single correct end point.

So `tests/compare_results.py` does not require search rows to equal the saved files. It requires the
paper's statement to hold, that no gap found exceeds half of the bound, and it reports how many rows
differ.
