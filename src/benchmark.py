"""Single-process timing of both rules (mean seconds per problem), grid's rho = 2, uniform lengths."""
import time, zlib, json, platform, numpy as np
from run_grid import draw_x
from shapdp import shapley_opt_div, serial_div
rows = []
for n in [5, 10, 20, 50, 100]:
    for k in [2, 16]:
        ts = te = 0.0
        for rep in range(20):
            rng = np.random.default_rng(zlib.crc32(f"{n}-{k}-2-uniform-{rep}".encode()))
            l = np.maximum(1, np.rint(k * 2 * draw_x("uniform", n, rng))).astype(int).tolist()
            t = time.perf_counter(); shapley_opt_div(l, k); ts += time.perf_counter() - t
            t = time.perf_counter(); serial_div(l, k); te += time.perf_counter() - t
        rows.append(dict(n=n, k=k, shapley_s=ts / 20, serial_s=te / 20))
        print(n, k, f"Shapley {ts/20:.5f} s, serial {te/20:.6f} s", flush=True)
json.dump(rows, open("benchmark.json", "w"), indent=1)
print(platform.python_version(), np.__version__)
