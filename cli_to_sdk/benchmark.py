#!/usr/bin/env python3
"""
Benchmark script for ripgrep SDK tiers.

Compares:
- Tier A: ripgrep_sdk (subprocess with streaming JSON)
- Baseline: Direct subprocess call
- ripgrepy: Third-party subprocess wrapper
"""

import json
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import List, Callable, Any

# Add SDK to path
sys.path.insert(0, str(Path(__file__).parent))

from ripgrep_sdk import Ripgrep, Match


@dataclass
class BenchmarkResult:
    name: str
    iterations: int
    cold_start_ms: float
    warm_mean_ms: float
    warm_p50_ms: float
    warm_p99_ms: float
    results_count: int
    throughput_ops_per_sec: float


def benchmark(
    name: str,
    func: Callable[[], Any],
    iterations: int = 50,
    warmup: int = 3,
) -> BenchmarkResult:
    """Run benchmark and collect statistics."""

    # Cold start
    start = time.perf_counter()
    result = func()
    results_count = len(list(result)) if hasattr(result, '__iter__') else 0
    cold_start_ms = (time.perf_counter() - start) * 1000

    # Warmup
    for _ in range(warmup):
        list(func())

    # Measure
    times_ms = []
    for _ in range(iterations):
        start = time.perf_counter()
        list(func())
        elapsed_ms = (time.perf_counter() - start) * 1000
        times_ms.append(elapsed_ms)

    times_ms.sort()
    mean_ms = sum(times_ms) / len(times_ms)
    p50_ms = times_ms[len(times_ms) // 2]
    p99_ms = times_ms[int(len(times_ms) * 0.99)]

    return BenchmarkResult(
        name=name,
        iterations=iterations,
        cold_start_ms=cold_start_ms,
        warm_mean_ms=mean_ms,
        warm_p50_ms=p50_ms,
        warm_p99_ms=p99_ms,
        results_count=results_count,
        throughput_ops_per_sec=1000 / mean_ms if mean_ms > 0 else 0,
    )


def format_results(results: List[BenchmarkResult]) -> str:
    """Format benchmark results as table."""
    lines = []
    lines.append("=" * 80)
    lines.append("BENCHMARK RESULTS")
    lines.append("=" * 80)
    lines.append("")

    # Header
    lines.append(
        f"{'Name':<30} {'Cold':>10} {'Mean':>10} {'P50':>10} {'P99':>10} {'Ops/s':>10}"
    )
    lines.append("-" * 80)

    for r in results:
        lines.append(
            f"{r.name:<30} {r.cold_start_ms:>9.2f}ms {r.warm_mean_ms:>9.2f}ms "
            f"{r.warm_p50_ms:>9.2f}ms {r.warm_p99_ms:>9.2f}ms {r.throughput_ops_per_sec:>9.1f}"
        )

    lines.append("-" * 80)
    lines.append(f"Results count: {results[0].results_count} matches")
    lines.append(f"Iterations: {results[0].iterations}")
    lines.append("")

    # Comparison
    if len(results) >= 2:
        baseline = results[0]
        lines.append("Comparison vs first result:")
        for r in results[1:]:
            speedup = baseline.warm_mean_ms / r.warm_mean_ms
            lines.append(f"  {r.name}: {speedup:.2f}x {'faster' if speedup > 1 else 'slower'}")

    return "\n".join(lines)


def main():
    # Test parameters
    pattern = "fn"  # Common pattern in Rust code
    search_path = "/home/user/ripgrep"  # ripgrep source

    print(f"Benchmarking pattern '{pattern}' in {search_path}")
    print()

    results = []

    # Tier A: ripgrep_sdk
    print("Testing: ripgrep_sdk (Tier A)...")
    rg = Ripgrep()

    def tier_a():
        return list(rg.search(pattern, search_path, file_type=["rust"]))

    results.append(benchmark("ripgrep_sdk (Tier A)", tier_a))

    # Baseline: Direct subprocess with JSON
    print("Testing: Direct subprocess...")

    def direct_subprocess():
        proc = subprocess.Popen(
            ["rg", "--json", "-t", "rust", pattern, search_path],
            stdout=subprocess.PIPE,
        )
        matches = []
        for line in proc.stdout:
            data = json.loads(line)
            if data.get("type") == "match":
                matches.append(data)
        proc.wait()
        return matches

    results.append(benchmark("Direct subprocess", direct_subprocess))

    # Direct subprocess without JSON (just counting)
    print("Testing: Direct subprocess (no parse)...")

    def direct_no_parse():
        proc = subprocess.Popen(
            ["rg", "--json", "-t", "rust", pattern, search_path],
            stdout=subprocess.PIPE,
        )
        count = sum(1 for line in proc.stdout if b'"type":"match"' in line)
        proc.wait()
        return [None] * count

    results.append(benchmark("Direct (no JSON parse)", direct_no_parse))

    # Subprocess with -l (files only)
    print("Testing: Files only mode...")

    def files_only():
        proc = subprocess.Popen(
            ["rg", "-l", "-t", "rust", pattern, search_path],
            stdout=subprocess.PIPE,
        )
        files = proc.stdout.read().decode().strip().split("\n")
        proc.wait()
        return files

    results.append(benchmark("Files only (-l)", files_only))

    # Try ripgrepy if available
    try:
        from ripgrepy import Ripgrepy

        print("Testing: ripgrepy...")
        rg_py = Ripgrepy(pattern, search_path).type("rust")

        def ripgrepy_test():
            return rg_py.run().as_dict

        results.append(benchmark("ripgrepy", ripgrepy_test))
    except ImportError:
        print("ripgrepy not available, skipping...")

    # Print results
    print()
    print(format_results(results))

    # Additional micro-benchmarks
    print()
    print("=" * 80)
    print("MICRO-BENCHMARKS")
    print("=" * 80)
    print()

    # Measure subprocess overhead
    print("Subprocess overhead (calling 'true'):")
    times = []
    for _ in range(100):
        start = time.perf_counter()
        subprocess.run(["true"], capture_output=True)
        times.append((time.perf_counter() - start) * 1000)
    print(f"  Mean: {sum(times)/len(times):.2f}ms")
    print(f"  Min: {min(times):.2f}ms")
    print(f"  Max: {max(times):.2f}ms")
    print()

    # Measure rg startup
    print("ripgrep startup (--version):")
    times = []
    for _ in range(50):
        start = time.perf_counter()
        subprocess.run(["rg", "--version"], capture_output=True)
        times.append((time.perf_counter() - start) * 1000)
    print(f"  Mean: {sum(times)/len(times):.2f}ms")
    print(f"  Min: {min(times):.2f}ms")
    print(f"  Max: {max(times):.2f}ms")
    print()

    # JSON parsing overhead
    print("JSON parsing overhead (1000 lines):")
    sample_line = b'{"type":"match","data":{"path":{"text":"src/main.rs"},"lines":{"text":"fn main() {}"},"line_number":1,"absolute_offset":0,"submatches":[{"match":{"text":"fn"},"start":0,"end":2}]}}'
    lines = [sample_line] * 1000

    times = []
    for _ in range(100):
        start = time.perf_counter()
        for line in lines:
            json.loads(line)
        times.append((time.perf_counter() - start) * 1000)
    print(f"  Mean: {sum(times)/len(times):.2f}ms for 1000 lines")
    print(f"  Per line: {sum(times)/len(times)/1000*1000:.2f}µs")


if __name__ == "__main__":
    main()
