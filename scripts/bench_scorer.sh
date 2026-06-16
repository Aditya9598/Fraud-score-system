#!/usr/bin/env bash
# Benchmark scorer throughput (in-process via cargo test)
set -euo pipefail
cd "$(dirname "$0")/../scorer"
source "$HOME/.cargo/env" 2>/dev/null || true
echo "Running scorer throughput benchmark (50000 iterations)..."
cargo test bench_score_throughput --release -- --nocapture 2>&1 | tail -5
