"""Runs the whole study from the seeds and compares every output with the saved files.
Usage: python src/reproduce_all.py
Fresh outputs go to outputs/; data/ and results/ are not touched."""
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "outputs"
STEPS = [("shapdp.py", "shapdp.log"),
         ("run_grid.py", "run_grid.log"),
         ("summarize.py", "summarize.log"),
         ("make_fig.py", "make_fig.log"),
         ("adversarial_search.py", "adversarial_search.log"),
         ("adversarial_search_n16.py", "adversarial_search_n16.log"),
         ("pilot_pessimistic.py", "pilot_output.txt")]


def main():
    OUT.mkdir(exist_ok=True)
    for script, log_name in STEPS:
        start = time.time()
        with open(OUT / log_name, "w") as log:
            subprocess.run([sys.executable, str(ROOT / "src" / script)], cwd=OUT, check=True,
                           stdout=log, stderr=subprocess.STDOUT)
        print(f"{script}: {time.time() - start:.0f} s", flush=True)
    return subprocess.run([sys.executable, str(ROOT / "tests" / "compare_results.py"), str(OUT)]).returncode


if __name__ == "__main__":
    sys.exit(main())
