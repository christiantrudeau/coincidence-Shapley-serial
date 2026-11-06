"""Larger-n adversarial search: does max_i |Sh_i - Ser_i| ever exceed n(k-1)/(2k), half the bound of
Proposition 2?  gap_over_bound = gap / (n(k-1)/k); a value of 0.5 means half of the bound."""
import random, json
from adversarial_search import climb
if __name__ == "__main__":
    rng = random.Random(11); out = []
    for k in [2, 3, 4, 8]:
        for n in [10, 12, 16]:
            res = max((climb(n, k, 4 * k, "g_bound", rng, iters=500) for _ in range(5)), key=lambda t: t[0])
            out.append(dict(k=k, n=n, ratio_to_half_bound=2 * res[0] * 2, gap_over_bound=2 * res[0], l=res[1]))
            print(k, n, "gap/(n(k-1)/k) =", round(2 * res[0], 4), res[1], flush=True)
    json.dump(out, open("adv2_results.json", "w"), indent=1)
