#!/usr/bin/env python3
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from oac.adapters import AdapterOptions, get_adapter  # noqa: E402
from oac.capsule import load_capsule  # noqa: E402
from oac.evals import evaluate_capsule  # noqa: E402

EXAMPLE = ROOT / "examples" / "hello-capsule"


def benchmark():
    capsule = load_capsule(EXAMPLE)
    targets = [t.name.value for t in capsule.manifest.targets if t.enabled]

    print(f"Benchmarking OAC across {len(targets)} targets...")
    print("-" * 40)

    results = {}

    for target_name in targets:
        print(f"Target: {target_name}")
        adapter = get_adapter(target_name)

        # 1. Hydrate Benchmark
        with tempfile.TemporaryDirectory() as tmp_dir:
            dest = Path(tmp_dir) / target_name
            start = time.perf_counter()
            for _ in range(5):
                adapter.hydrate(EXAMPLE, dest, AdapterOptions())
            avg_hydrate = (time.perf_counter() - start) / 5
            print(f"  Avg Hydrate: {avg_hydrate:.4f}s")

            # 2. Ingest Benchmark
            start = time.perf_counter()
            for _ in range(5):
                adapter.ingest(dest, EXAMPLE, AdapterOptions())
            avg_ingest = (time.perf_counter() - start) / 5
            print(f"  Avg Ingest:  {avg_ingest:.4f}s")

            results[target_name] = {"hydrate": avg_hydrate, "ingest": avg_ingest}

    # 3. Eval Benchmark
    print("-" * 40)
    print("Eval (Full Capsule):")
    start = time.perf_counter()
    for _ in range(3):
        evaluate_capsule(EXAMPLE)
    avg_eval = (time.perf_counter() - start) / 3
    print(f"  Avg Eval: {avg_eval:.4f}s")

    print("-" * 40)
    print("Done.")


if __name__ == "__main__":
    benchmark()
